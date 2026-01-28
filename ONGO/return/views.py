from django.shortcuts import redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
# from django.views.decorators.cache import never_cache

# from django.utils.decorators import method_decorator

from django.views import View

from django.shortcuts import get_object_or_404
from django.db import transaction

# from django.http import JsonResponse
from order.models import Order
from .models import Return, ReturnItem

from django.contrib import messages

import logging

logger = logging.getLogger(__name__)


class ReturnOrderView(LoginRequiredMixin, View):

    template_name = 'returns/return_order.html'

    def get(self, request, order_id):
        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        if order.status != 'delivered':
            messages.error(request, "This order cannot be returned.")
            return redirect('order_detail', order_id=order_id)

        order_items = order.items.all()
        if not order_items.exists():
            messages.error(request, "This order has no items to return.")
            return redirect('order_detail', order_id=order_id)

        context = {
            'order': order,
            'order_items': order_items,
        }

        return render(request, self.template_name, context)

    def post(self, request, order_id):

        order = get_object_or_404(Order, order_id=order_id, user=request.user)

        if order.status != 'delivered':
            messages.error(request, "This order cannot be returned.")
            return redirect('order_detail', order_id=order_id)

        return_reason = request.POST.get('return_reason', '').strip()
        if not return_reason:
            messages.error(request, "Please provide a reason for the return.")
            return redirect('order_detail', order_id=order_id)

        selected_items = []
        for order_item in order.items.all():
            item_key = f'item_{order_item.id}'
            if request.POST.get(f'{item_key}_select'):
                try:
                    quantity = int(request.POST.get(f'{item_key}_quantity', 0))
                    item_reason = request.POST.get(f'{item_key}_reason', '').strip()

                    if quantity <= 0 or quantity > order_item.quantity:
                        messages.error(
                            request,
                            f"Invalid quantity for {order_item.product.name}."
                        )
                        return redirect('order_detail', order_id=order_id)

                    total_returned = ReturnItem.objects.filter(
                        order_item=order_item,
                        return_request__status__in=['pending', 'accepted']
                    ).aggregate(total=Sum('quantity'))['total'] or 0

                    print(total_returned)

                    if total_returned + quantity > order_item.quantity:
                        messages.error(
                            request,
                            f"Cannot return {quantity} more units of {order_item.product_name}. "
                            f"Only {order_item.quantity - total_returned} units available for return."
                        )
                        return redirect('order_detail', order_id=order_id)

                    selected_items.append({
                        'order_item': order_item,
                        'quantity': quantity,
                        'item_reason': item_reason
                    })

                except (ValueError, TypeError):
                    logger.error(request, 'User enterd invalid input')
                    messages.error(request, "Invalid input for item quantities.")
                    return redirect('order_detail', order_id=order_id)

        if not selected_items:
            messages.error(request, "Please select at least one item to return.")
            return redirect('order_detail', order_id=order_id)

        try:
            with transaction.atomic():
                return_request = Return.objects.create(
                    user=request.user,
                    order=order,
                    return_reason=return_reason,
                    status='pending'
                )

                for item_data in selected_items:
                    ReturnItem.objects.create(
                        return_request=return_request,
                        order_item=item_data['order_item'],
                        quantity=item_data['quantity'],
                        item_reason=item_data['item_reason'] or return_reason
                    )

            messages.success(
                request,
                "Your return request has been submitted successfully!"
            )
            return redirect('order_list')

        except Exception as e:
            logger.error(request, f'Something went wrong while retutn order requesting: {e}')
            messages.error(request, "An error occurred while processing your return request.")
            return redirect('order_detail', order_id=order_id)
