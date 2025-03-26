from django.db.models import Count
from itertools import count
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from django.shortcuts import render, redirect, HttpResponse
from django.views import View
from django.http import JsonResponse
from .forms import CustomerRegistrationForm, CustomerProfileForm
from django.db.models import Q
from .models import Customer, Product, Cart, OrderPlaced
from django.core.mail import send_mail
import razorpay
from django.views.decorators.csrf import csrf_exempt


def home(request):
 return render(request, 'app/home.html')

def about(request):
 return render(request, 'app/about.html')

def contact(request):
 return render(request, 'app/contact.html')


class CategoryView(View):
    def get(self,request,val):
        product = Product.objects.filter(category=val)
        title = Product.objects.filter(category=val).values('title')
        return render(request,"app/category.html",locals())
    
class CategoryTitle(View):
    def get(self, request, val):
        product = Product.objects.filter(title=val)
        title =   Product.objects.filter(category=product[0].category).values('title')
        return render(request,"app/category.html",locals())


class ProductView(View):
	def get(self, request):
		totalitem = 0
		mens = Product.objects.filter(category='M')
		womens = Product.objects.filter(category='W')
		kids = Product.objects.filter(category='K')
		if request.user.is_authenticated:
			totalitem = len(Cart.objects.filter(user=request.user))
		return render(request, 'app/home.html', {'mens':mens, 'womens':womens, 'kids':kids, 'totalitem':totalitem})

#def product_detail(request):
# return render(request, 'app/productdetail.html')

class ProductDetailView(View):
 def get(self,request,pk):
    product = Product.objects.get(pk=pk)
    return render(request,  'app/product-detail.html.', locals())
 
 

#from django.shortcuts import redirect
#from django.contrib.auth.decorators import login_required
#from django.contrib import messages
#from django.db.models import Q
#from app.models import Cart, Product # # Import your models if not already imported

#@login_required  # Ensures only authenticated users can access this view
def add_to_cart(request):
    user = request.user
    product_id = request.GET.get('prod_id')
    
    if not product_id:
        messages.error(request, "Invalid product ID.")
        return redirect('/cart')
    
    try:
        # Check if the product exists
        product = Product.objects.get(id=product_id)
        
        # Check if the product is already in the user's cart
        item_already_in_cart = Cart.objects.filter(Q(product=product) & Q(user=user)).exists()
        
        if not item_already_in_cart:
            # Add the product to the cart
            Cart.objects.create(user=user, product=product)
            messages.success(request, 'Product Added to Cart Successfully!!')
        else:
            messages.info(request, 'This product is already in your cart.')
        
    except Product.DoesNotExist:
        messages.error(request, "Product not found.")
    
    return redirect('/cart')


    
def show_cart(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    amount = 0
    for p in cart:
        value = p.quantity * p.product.discounted_price
        amount = amount + value
        totalamount = amount + 40
    return render(request, 'app/addtocart.html', locals())

#@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    cart_item.delete()
    messages.success(request, f"{cart_item.product.title} has been removed from your cart.")
    return redirect('/cart')

#@login_required
def increase_quantity(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    print("cart")
    print(cart_item.product)
    print()
    cart_item.quantity += 1
    cart_item.save()
    messages.success(request, f"Quantity of {cart_item.product.title} has been increased.")
    return redirect('/cart')

#@login_required
def decrease_quantity(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    
    if cart_item.quantity > 1:  # Prevent going below 1
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, f"Quantity of {cart_item.product.title} has been decreased.")
    else:
        messages.warning(request, "Quantity cannot be less than 1.")
    
    return redirect('/cart')

def buy_now(request):
 return render(request, 'app/buynow.html')

def profile(request):
 return render(request, 'app/profile.html')

def address(request):
   add = Customer.objects.filter(user=request.user)
   return render(request, 'app/address.html' ,locals())
 

def orders(request):
	order_placed = OrderPlaced.objects.filter(user=request.user)
	return render(request, 'app/orders.html', locals())

def change_password(request):
 return render(request, 'app/changepassword.html')

def mobile(request, data=None):
    if data is None:
        mobiles = Product.objects.filter(category='M')
    elif data in ['Redmi', 'Samsung']:
        mobiles = Product.objects.filter(category='M').filter(brand=data)
    elif data == 'below':
               mobiles = Product.objects.filter(category='M').filter(discounted_price__lt=10000)
    elif data == 'above':
               mobiles = Product.objects.filter(category='M').filter(discounted_price__gt=10000)

    else:
        mobiles = []  # Optional: handle case where data is not recognized

    return render(request, 'app/mobile.html', {'mobiles': mobiles})

def login(request):
 return redirect('/login')
 return render(request, 'app/login.html')


class CustomerRegistrationView(View):
 def get(self, request):
  form = CustomerRegistrationForm()
  return render(request, 'app/customerregistration.html', {'form':form})
  
 def post(self, request):
  form = CustomerRegistrationForm(request.POST)
  if form.is_valid():
   messages.success(request, 'Congratulations!! Registered Successfully.')
   form.save()
  return render(request, 'app/customerregistration.html', {'form':form})

  

def checkout(request):
    user = request.user
    add = Customer.objects.filter(user=user)
    cart_items = Cart.objects.filter(user=request.user)
    amount = 0.0
    shipping_amount = 40.0
    totalamount = 0.0

    cart_product = [p for p in cart_items]
    if cart_product:
        for p in cart_product:
            tempamount = p.quantity * p.product.discounted_price
            amount += tempamount
        totalamount = amount + shipping_amount

    context = {
        'add': add,
        'cart_items': cart_items,
        'totalamount': totalamount,
    }
    return render(request, 'app/checkout.html', context)



class ProfileView(View):
	def get(self, request):
		form = CustomerProfileForm()
		return render(request, 'app/profile.html', locals())
		
	def post(self, request):
		form = CustomerProfileForm(request.POST)
		if form.is_valid():
			user = request.user
			name  = form.cleaned_data['name']
			locality = form.cleaned_data['locality']
			city = form.cleaned_data['city']
			state = form.cleaned_data['state']
			zipcode = form.cleaned_data['zipcode']
			reg = Customer(user=user, name=name, locality=locality, city=city, state=state, zipcode=zipcode)
			reg.save()
			messages.success(request, 'Congratulations!! Profile Updated Successfully.')
		return render(request, 'app/profile.html', locals())


# @csrf_exempt
# def confirm_order(request):
    # user = request.user
    # payment_order_id = request.session.get('payment_order_id')
    # address_id = request.session.get('address_id')
    # address = address.objects.get(id=address_id, user=user)

    # Save orders
    # cart_items = Cart.objects.filter(uid=user)
    # for item in cart_items:
        # orders.objects.create(
            # order_id=payment_order_id,
            # uid=user,
            # pid=item.pid,
            # qty=item.qty,
            # current_status="Order Placed",
        # )

    # Clear cart and session data
    # cart_items.delete()
    # request.session.pop('payment_order_id', None)
    # request.session.pop('address_id', None)

    # # Add a success message
    # messages.success(request, "Your order has been placed successfully!")
    # return redirect('/home')

def payment_done(request):
    custid = request.GET.get('custid')  # Get the customer ID from the URL
    user = request.user  # Get the current logged-in user
    cart_items = Cart.objects.filter(user=user)  # Get the user's cart items
    customer = Customer.objects.get(id=custid)  # Get the customer object by ID

    # Ensure we have valid cart items and the customer exists
    if not cart_items.exists():
        messages.error(request, "No items found in the cart.")
        return redirect('/cart')
    
    # Loop through each item in the cart and create an order for each
    for item in cart_items:
        # Create the order in the OrderPlaced model
        OrderPlaced(user=user, customer=customer, product=item.product, quantity=item.quantity).save()
        
        # After the order is created, delete the cart item to clear the cart
        item.delete()
    # Success message after the order is placed
    messages.success(request, "Your order has been placed successfully!")
    
    # Redirect the user to the orders page
    return redirect("orders")         



def search(request):
    query = request.GET.get('search', '').strip()
    print(f"Search query: {query}")  # Debug: Print the search query
    if query:
        product = Product.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
        print(f"Products found: {product}")  # Debug: Print the filtered products
    else:
        product = []
    return render(request, "app/search.html", {'product': product, 'query': query})


