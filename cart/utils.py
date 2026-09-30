# apps/cart/utils.py

from .models import Cart, CartItem


def get_or_create_cart(request):
    """
    Resolve the current request's active cart.

    - Authenticated users get a cart tied to their account.
    - Anonymous users get a cart tied to their Django session key.
    - If a logged-in user still has a guest cart from before they signed
      in (same browser session), it is merged into their account cart
      automatically so nothing added while browsing as a guest is lost.
    """
    if request.user and request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user, is_active=True)

        session_key = request.session.session_key
        if session_key:
            guest_cart = (
                Cart.objects
                .filter(session_key=session_key, is_active=True, user__isnull=True)
                .first()
            )
            if guest_cart:
                merge_cart_into(guest_cart, cart)

        return cart

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    cart, _ = Cart.objects.get_or_create(
        session_key=session_key, user=None, is_active=True
    )
    return cart


def merge_cart_into(source_cart, target_cart):
    """
    Move every line item from source_cart into target_cart, combining
    quantities where the same product + customization already exists,
    then discard the now-empty source cart.
    """
    for item in source_cart.items.all():
        existing = target_cart.items.filter(
            product=item.product, customization=item.customization
        ).first()

        if existing:
            existing.quantity += item.quantity
            existing.save(update_fields=['quantity', 'updated_at'])
        else:
            CartItem.objects.create(
                cart=target_cart,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                customization=item.customization,
                note=item.note,
            )

    source_cart.delete()