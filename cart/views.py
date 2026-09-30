from django.shortcuts import render

# Create your views here.
# apps/cart/views.py

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import CartItem
from .serializers import (
    CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer
)
from .utils import get_or_create_cart


class CartViewSet(viewsets.ViewSet):
    """
    Shopping cart for both guest (session-based) and authenticated users.
    There is always exactly one cart per request — it is created on first
    touch and resolved automatically, so the client never has to know or
    pass a cart id.

    GET    /api/cart/                    -> current cart, items & totals
    POST   /api/cart/add_item/           -> add a product (merges qty if already in cart)
    PATCH  /api/cart/items/{item_id}/    -> change a line item's quantity
    DELETE /api/cart/items/{item_id}/    -> remove a line item
    POST   /api/cart/clear/              -> empty the cart
    POST   /api/cart/sync_prices/        -> refresh stale prices to current product prices
    """
    permission_classes = [IsAuthenticated]

    def _cart_response(self, request, cart, extra=None, status_code=status.HTTP_200_OK):
        payload = {
            'success': True,
            'data': CartSerializer(cart, context={'request': request}).data,
        }
        if extra:
            payload.update(extra)
        return Response(payload, status=status_code)

    # ============================================
    # GET /api/cart/
    # ============================================
    def list(self, request):
        cart = get_or_create_cart(request)
        return self._cart_response(request, cart)

    # ============================================
    # POST /api/cart/add_item/
    # ============================================
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart = get_or_create_cart(request)
        serializer = AddCartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        product = serializer.context['product']
        quantity = serializer.validated_data['quantity']
        customization = serializer.validated_data.get('customization') or {}
        note = serializer.validated_data.get('note', '')

        with transaction.atomic():
            existing = cart.items.select_for_update().filter(
                product=product, customization=customization
            ).first()

            if existing:
                new_quantity = existing.quantity + quantity
                if not product.is_available_for_order(new_quantity):
                    return Response({
                        'success': False,
                        'error': f'Only {product.quantity} unit(s) available in total; '
                                 f'you already have {existing.quantity} in your cart.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                existing.quantity = new_quantity
                existing.save(update_fields=['quantity', 'updated_at'])
            else:
                CartItem.objects.create(
                    cart=cart,
                    product=product,
                    quantity=quantity,
                    unit_price=product.final_price,
                    customization=customization,
                    note=note,
                )

        return self._cart_response(
            request, cart,
            extra={'message': 'Item added to cart'},
            status_code=status.HTTP_201_CREATED,
        )

    # ============================================
    # PATCH  /api/cart/items/{item_id}/
    # DELETE /api/cart/items/{item_id}/
    # ============================================
    @action(detail=False, methods=['patch', 'delete'], url_path='items/(?P<item_id>[^/.]+)')
    def item_detail(self, request, item_id=None):
        cart = get_or_create_cart(request)
        item = get_object_or_404(CartItem, id=item_id, cart=cart)

        if request.method == 'DELETE':
            item.delete()
            return self._cart_response(request, cart, extra={'message': 'Item removed from cart'})

        serializer = UpdateCartItemSerializer(data=request.data, context={'item': item})
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data['quantity']
        item.save(update_fields=['quantity', 'updated_at'])
        return self._cart_response(request, cart, extra={'message': 'Quantity updated'})

    # ============================================
    # POST /api/cart/clear/
    # ============================================
    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = get_or_create_cart(request)
        cart.items.all().delete()
        return self._cart_response(request, cart, extra={'message': 'Cart cleared'})

    # ============================================
    # POST /api/cart/sync_prices/
    # Refreshes any line whose stored price has drifted from the
    # product's live price — call this before checkout.
    # ============================================
    @action(detail=False, methods=['post'])
    def sync_prices(self, request):
        cart = get_or_create_cart(request)
        updated = 0
        for item in cart.items.select_related('product'):
            if item.price_changed:
                item.unit_price = item.current_unit_price
                item.save(update_fields=['unit_price', 'updated_at'])
                updated += 1
        return self._cart_response(request, cart, extra={'updated_items': updated})