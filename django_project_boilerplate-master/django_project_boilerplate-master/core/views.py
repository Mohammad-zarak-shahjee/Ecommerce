from django.conf import settings
from django.shortcuts import render ,get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
#importing our models to use their field in the context
from .models import Item,Order,OrderItem,BillingAddress,Payment,Coupon,Refund
from django.utils import timezone
from django.shortcuts import redirect
from django.urls import reverse
from .forms import CheckoutForm,CouponForm,RefundForm
import stripe
import random 
import string
# Create your views here.

#stripe.api_key = settings.STRIPE_SECRET_KEY
#used for authenticate with stripe
stripe.api_key = 'your stripe secret key'


def create_ref_code():
    #it would create a random seq of characters 
    #k =  special argument for length of string
    return ''.join(random.choices(string.ascii_lowercase + string.digits,k = 20))


class HomeView(ListView):
    model = Item
    paginate_by =10
    template_name = "home-page.html"


class OrderSummaryView(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            context = {
                'object': order
            }
            return render(self.request,'order_summary.html',context)
        except ObjectDoesNotExist:
            messages.warning(self.request,"You don't have an active order,Buy something!")
            return redirect("/")
    

class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

class CheckoutView(View):
    #get the request with arbitary no of arguments
    def get(self,*args,**kwargs):
        try:
        
            order = Order.objects.get(user=self.request.user,ordered=False)  
            #form
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform':CouponForm(),
                'order':order,
                'DISPLAY_COUPON_FORM':True
                
            }
            return render(self.request,"checkout.html",context)
        
        except ObjectDoesNotExist:
            messages.info(request,"You do not have an active order" )
            return redirect("core:checkout")
        

    def post(self,*args,**kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            if form.is_valid():
                street_address = form.cleaned_data.get('street_address')
                house_address = form.cleaned_data.get('house_address')
                country = form.cleaned_data.get('country')
                zip = form.cleaned_data.get('zip')
                #add functionality to below commented fields if you can
                #same_shipping_address =form.cleaned_data.get('same_billing_address')
                #save_info = form.cleaned_data.get('save_info')
                payment_option = form.cleaned_data.get('payment_option')
                billing_address = BillingAddress(
                    user = self.request.user,
                    street_address=street_address,
                    house_address = house_address,
                    country = country,
                    zip = zip,
                )
                billing_address.save()
                order.billing_address = billing_address
                order.save()
                if payment_option == 'S':
                    return redirect('core:payment',payment_option='stripe')
                elif payment_option == 'P':
                    return redirect('core:payment',payment_option='paypal')
                elif payment_option == 'C':
                    #creating payment
                    payment = Payment() 
                    payment.stripe_charge_id = random.vonmisesvariate(0,4)
                    payment.user = self.request.user
                    payment.amount  = order.get_total()
                    payment.save() 
                    
                    ######for fixing the order quantity for next order of same item#####
                    order_items = order.items.all()
                    order_items.update(ordered=True)
                    #doing the loop for each orderitem 
                    for item in order_items:
                        item.save()
                    ##########fixing end ############################
                    #assigning the payment to order
                    order.ordered =True
                        #this is the payment field of order model 
                    order.payment = payment
                    order.ref_code =create_ref_code()
                    order.save()
                    messages.success(self.request,"Order Successfully placed.Keep your Cash ready!")
                    return redirect("/",payment_option='Cash-On-Delivery')
                    

                elif payment_option == 'D':
                    return redirect('core:payment',payment_option='Debitcard')
                else:
                    messages.warning(self.request,"invalid payment option")
                    return redirect("core:checkout")

        except ObjectDoesNotExist:
            messages.warning(self.request,"You don't have an active order,Buy something!")
            return redirect("core:order-summary")
        print(self.request.POST)


class PaymentView(View):
    def get(self, *args,**kwargs):
        order = Order.objects.get(user=self.request.user,ordered=False)
        #restricting to go to payment pg without a billing address
        if order.billing_address:
            context = {
                'order': order,
                'DISPLAY_COUPON_FORM':False
            }
            return render(self.request,"payment.html",context)
        else:
            messages.warning(self.request,"You have not added a billing address Buddy!")
            return redirect("core:checkout")
            

    def post(self, *args,**kwargs):
        #we get the order so that we can get the total amount for the order done below in our amount variable
        order = Order.objects.get(user=self.request.user,ordered=False)
        #stripetoken is a token ID  that we insert into the form so it gets submitted to the server
        token = self.request.POST.get('stripeToken')
        print(token)
        amount = int(order.get_total() * 100)  #we multiply by 100 bcoz the orgnal value is in paisa so to convert it to rupees
       
       #create the payment
        payment = Payment() 
        payment.stripe_charge_id = random.vonmisesvariate(0,4)
        payment.user = self.request.user
        payment.amount  = order.get_total()
        payment.save() 
        
        #assign the payment to the order

        order_items = order.items.all()
        order_items.update(ordered=True)
        #doing the loop for each orderitem 
        for item in order_items:
            item.save()

        order.ordered =True
            #this is the payment field of order model 
        order.payment = payment
        order.ref_code =create_ref_code()
        order.being_delivered=True
        order.save()
        try:
            # Use Stripe's library to make requests..
            charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token,
               
            )            

        #creating the payment 
             #here we create payment as the object of the class (Model)Payment in Models.py
                    


        # assign the payment to the order
        #when we recieve the post req we not only create a charge(as done above)
        #but we need to create a logic for which it says the order has been successfully ordered
           
                            
            messages.success(self.request,"Your Order was Successfully placed. Be ready for delivery soon!")
        #redirect is used to go back to homepage after order succesffuly placed
            return redirect("/")

        except stripe.error.CardError as e:
        # Since it's a decline, stripe.error.CardError will be caught
        #we caught the error using json_body
            body = e.json_body
            err = body.get('error',{})
            messages.warning(self.request,f"{err.get('message')}")
        #redirect is used to go back to homepage after order succesffuly placed
            return redirect("/")
                            
        except stripe.error.RateLimitError as e:
        # Too many requests made to the API too quickly
            messages.warning(self.request,"Rate limit error")
            return redirect("/")
                        
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.success(self.request,"Your Order was Successfully placed. Be ready for delivery soon")
            return redirect("/")

        except stripe.error.AuthenticationError as e:
        # Authentication with Stripe's API failed
        # (maybe you changed API keys recently)
            messages.warning(self.request,"Not authenticated")
            return redirect("/")
                        
        except stripe.error.APIConnectionError as e:
        # Network communication with Stripe failed
            messages.warning(self.request,"Network error")
            return redirect("/")
                        
        except stripe.error.StripeError as e:
        # Display a very generic error to the user, and maybe send
        # yourself an email
            messages.warning(self.request,"Something went wrong. You were not charged . Please try again")
            return redirect("/")

        except Exception as e:
                        # Something else happened, completely unrelated to Stripe
            messages.warning(self.request,"A serious error occured,We have notified the developers")
            return redirect("/")
                    


      

       


   

#slug is used here to identify a specific item
@login_required
def add_to_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    #arg to get the specified item,then to get the user who has ordered,then last arg makes sure that we arnt getting a item 
    #that is already been purchase
    #as this returning a tuple we use two variables here
    order_item, created= OrderItem.objects.get_or_create(
        item=item,
        user = request.user,
        ordered=False
    )
    #we are filtering it so that we get the orders which are not completed as there can b orders which are compltd
    #and ordered field specifies orders whuch are compltd
    order_qs = Order.objects.filter(user=request.user,ordered=False)
    #if order exists
    if order_qs.exists():
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug =item.slug).exists():
            #if the above condtn is met that means the item is already in the cart
            order_item.quantity += 1
            order_item.save()
            messages.info(request,"This item quantity was updated nigga." )
            return redirect("core:order-summary")
        #if there isnt a order yet
        #it redirects to the same pg if it is the first order of the item
        else:
            messages.info(request,"This item was added to your cart Boss." )
            order.items.add(order_item)
            return redirect("core:product",slug=slug)

            

    #if order doesnt exists      
    else:
        ordered_date =timezone.now()
        order = Order.objects.create(user=request.user,ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request,"This item was added to your cart Boss." )
        #as this is a redirect func so kwargs not used but directly slug =slug
        return redirect("core:order-summary")

@login_required
def remove_from_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
        )

    #if order exists
    if order_qs.exists():
        #get that order
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug =item.slug).exists():
            order_item = OrderItem.objects.get_or_create(
                item=item,
                user = request.user,
                ordered=False
            )[0]
            order.items.remove(order_item)
            messages.info(request,"This item was removed from your cart Boss." )
            return redirect("core:order-summary")
        else:
            #add a msg saying the order does not contain the item
            messages.info(request,"This item was not in your cart Boss." )
            return redirect("core:product",slug=slug)
    else:
        #add amsg saying the user doesnt hve an order
        messages.info(request,"You do not have an active order" )
        return redirect("core:product",slug=slug)

    
@login_required
def remove_single_item_from_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
        )

    #if order exists
    if order_qs.exists():
        #get that order
        order = order_qs[0]
        #check if the order item is in the order
        if order.items.filter(item__slug =item.slug).exists():
            order_item = OrderItem.objects.get_or_create(
                item=item,
                user = request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            messages.info(request,"This item quantity was updated" )
            #we dont pass a slug here as order-summry url doesnt use slug 
            return redirect("core:order-summary")
        else:
            #add a msg saying the order does not contain the item
            messages.info(request,"This item was not in your cart Boss." )
            return redirect("core:product",slug=slug)
    else:
        #add amsg saying the user doesnt hve an order
        messages.info(request,"You do not have an active order" )
        return redirect("core:product",slug=slug)


#func for getting coupon in Addcoupon view

def get_coupon(request,code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon
    except ObjectDoesNotExist:
        messages.info(request,"This coupon does not exist" )
        return redirect("core:checkout")

#imp :we cant send a get request to the below class based view because we havnt defined a get func in it
class AddCouponView(View):
    ####for validation of form###
    ##here self is used to get the current instance of the class and access varbles of this class rather than the inherited View
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or None)
        if form.is_valid():
        #############validation ends####
            try:
                code =form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user,ordered=False)
                order.coupon =get_coupon(self.request,code)
                order.save()
                messages.success(self.request,"Coupon successfully applied" )
                return redirect("core:checkout")
                
            except ObjectDoesNotExist:
                messages.info(self.request,"You do not have an active order" )
                return redirect("core:checkout")
        
   
class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form' : form
        }
        return render(self.request,'request_refund.html',context)
    def post(self, *args, **kwargs):
        form =RefundForm(self.request.POST)
        if form.is_valid():
            #data from user in form 
            ref_code = form.cleaned_data.get('ref_code')
            message= form.cleaned_data.get('message')
            email =form.cleaned_data.get('email')
             #edit the order
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested=True
                order.save()

                #store the refund
                refund= Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request,"Your request is important to us! We are working on it asap.")
                return redirect("core:request-refund")

            
            except ObjectDoesNotExist:
                messages.info(self.request,"This order does not exist")
                return redirect("core:request-refund")
