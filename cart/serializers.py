# apps/cart/serializers.py

from rest_framework import serializers
from .models import Cart, CartItem
from products.models import Product
from products.serializers import ProductListSerializer


class CartItemSerializer(serializers.ModelSerializer):
    """Read serializer for a single cart line, including live product data."""

    product_detail = ProductListSerializer(source='product', read_only=True)
    line_total = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    current_unit_price = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    price_changed = serializers.BooleanField(read_only=True)
    stock_issue = serializers.BooleanField(read_only=True)
    max_available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'product_detail', 'quantity',
            'unit_price', 'current_unit_price', 'price_changed',
            'customization', 'note', 'line_total',
            'stock_issue', 'max_available_quantity',
            'added_at', 'updated_at',
        ]
        read_only_fields = ['id', 'unit_price', 'added_at', 'updated_at']


class CartSerializer(serializers.ModelSerializer):
    """Read serializer for the whole cart: items plus computed totals."""

    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    total_lines = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    delivery_total = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    grand_total = serializers.DecimalField(read_only=True, max_digits=12, decimal_places=2)
    has_price_changes = serializers.BooleanField(read_only=True)
    has_stock_issues = serializers.BooleanField(read_only=True)
    is_empty = serializers.BooleanField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'total_items', 'total_lines',
            'subtotal', 'delivery_total', 'grand_total',
            'has_price_changes', 'has_stock_issues', 'is_empty',
            'created_at', 'updated_at',
        ]


class AddCartItemSerializer(serializers.Serializer):
    """Validates the payload for POST /api/cart/add_item/."""

    product_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, default=1)
    customization = serializers.JSONField(required=False, default=dict)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or unavailable.")
        # stash the resolved product so validate() and the view don't re-query
        self.context['product'] = product
        return value

    def validate(self, data):
        product = self.context.get('product')
        quantity = data.get('quantity', 1)

        if not product.is_available:
            raise serializers.ValidationError({"product_id": "This product is not available for order."})

        if not product.is_available_for_order(quantity):
            if product.is_out_of_stock:
                raise serializers.ValidationError({"quantity": "This product is out of stock."})
            raise serializers.ValidationError(
                {"quantity": f"Only {product.quantity} unit(s) available."}
            )

        customization = data.get('customization') or {}
        if customization:
            self._validate_customization(product, customization)
        elif not product.is_customizable and customization:
            raise serializers.ValidationError(
                {"customization": "This product does not support customization."}
            )

        return data

    def _validate_customization(self, product, customization):
        if not product.is_customizable:
            raise serializers.ValidationError(
                {"customization": "This product does not support customization."}
            )
        options = product.customization_options or {}
        for key, value in customization.items():
            allowed_values = options.get(key)
            if allowed_values and value not in allowed_values:
                raise serializers.ValidationError(
                    {"customization": f"'{value}' is not a valid choice for '{key}'."}
                )


class UpdateCartItemSerializer(serializers.Serializer):
    """Validates the payload for PATCH /api/cart/items/{item_id}/."""

    quantity = serializers.IntegerField(min_value=1)

    def validate_quantity(self, value):
        item = self.context['item']
        if not item.product.is_available_for_order(value):
            raise serializers.ValidationError(
                f"Only {item.product.quantity} unit(s) available."
            )
        return value