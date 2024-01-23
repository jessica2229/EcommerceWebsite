import random
from django.shortcuts import redirect, render,HttpResponse
from . models import Product,CartItem,Order
from . forms import CreateUserForm,AddProduct
from django.contrib.auth import login,logout,authenticate
from django.contrib import messages
import razorpay

# Create your views here.
def index(request):
    products = Product.objects.all()
    context = {}
    context['products'] = products
    return render(request,"index.html",context)

def prodDetail(req,pid):
    products =  Product.objects.get(product_id = pid)
    context = {'products':products}
    return render(req,"productDetail.html",context)

def viewCart(req):
    if req.user.is_authenticated:
        allproducts = CartItem.objects.filter(user =  req.user)
    else:
        return redirect("/login")
    context = {}
    context['cart_items'] = allproducts
    total_price =0
    for x in allproducts:
        total_price += (x.product.price * x.quantity)
        print(total_price)
    context['total'] = total_price
    length  = len(allproducts)

    context['items'] = length
    return render(req,"cart.html",context)

def removeCart(req,pid):
    cart_item = CartItem.objects.filter(product_id = pid)
    cart_item.delete()
    return redirect("/viewCart")

def add_cart(req,pid):
    products = Product.objects.get(product_id = pid)
    user = req.user if req.user.is_authenticated else None
    print(products)
    if user:
        cart_item,created =CartItem.objects.get_or_create(product=products,user= user)
        print(cart_item,created)
    else:
        return redirect("/login")
        #cart_item,created =CartItem.objects.get_or_create(product=products)
    if not created:
        cart_item.quantity += 1
    else:
        cart_item.quantity = 1 
    cart_item.save()
    return redirect("/viewCart")

def range(req):
    if req.method == "GET":
        return redirect("/")
    else:
        r1 = req.POST.get("min")
        r2 = req.POST.get("max")
        print(r1,r2)
        if r1 is not None and r2 is not None and r1 != "" and r2 !="":
            queryset = Product.objects.filter(price__range = (r1,r2))
            #Custome Manager
            #queryset = Product.prod.get_price_range(r1,r2)
            print(queryset)
            context= {'products':queryset}
            return render(req,"index.html",context)
        else:
            queryset = Product.objects.all()
            context= {'products':queryset}
            return render(req,"index.html",context)
        
def watchList(req):
    queryset =Product.prod.watch_list()
    print(queryset)
    context= {'products':queryset}
    
    return render(req,"index.html",context)

def sort(req):
    queryset = Product.objects.all().order_by("price")
    context= {'products':queryset}
    return render(req,"index.html",context)

def HightoLow(req):
    #Default Manager
    queryset = Product.objects.all().order_by("-price")
    #Custom Manager
    #queryset = Product.prod.price_order()
    context= {'products':queryset}
    return render(req,"index.html",context)

def updatqty(req,uval,pid):
    #products = Product.objects.get(product_id = pid)
    user = req.user
    c = CartItem.objects.filter(product_id = pid,user = user)
    print(c)
    print(c[0])
    print(c[0].quantity)
    if uval == 1:
        a = c[0].quantity + 1
        c.update(quantity = a)

        print(c[0].quantity)
    else:
        a = c[0].quantity - 1
        c.update(quantity = a)
        print(c[0].quantity)
    return redirect("/viewCart")

def register_user(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,("User Created Successfully"))
            return redirect("/login")
        else:
            messages.error(request,"Incorrect Password Format")
    context = {'form':form}
    return render(request,"register.html",context)

def login_user(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request,username=username,password=password)
        if user is not None:
            login(request,user)
            messages.success(request,("You have been logged in!!"))
            return redirect("/")
        else:
            messages.error(request,"Incorrect Username or Password")
            return redirect("/login")
    else:
        return render(request,"login.html")

def logout_user(request):
    logout(request)
    messages.success(request,("You have logged out Successfully"))
    return redirect("/")

def viewOrder(req):
    c = CartItem.objects.filter(user = req.user)#1
    """ oid = random.randrange(1000,9999)
    for x in c:
        Order.objects.create(order_id = oid,product_id = x.product.product_id, user = req.user, quantity = x.quantity)#2
    orders = Order.objects.filter(user = req.user,is_completed = False)  """
    context = {}
    context['cart_items'] = c
    total_price =0
    for x in c:
        total_price += (x.product.price * x.quantity)
        print(total_price)
    context['total'] = total_price
    length  = len(c)
    context['items'] = length
    return render(req,"viewOrder.html",context)

def makePayment(req):
    c = CartItem.objects.filter(user=req.user)
    oid = random.randrange(1000,9999)
    for x in c:
        Order.objects.create(order_id = oid,product_id = x.product.product_id, user = req.user, quantity = x.quantity)#2
    orders = Order.objects.filter(user = req.user,is_completed = False) 
    total_price =0
    for x in orders:
        total_price += (x.product.price * x.quantity)
        oid = x.order_id
        print(oid)
    client = razorpay.Client(auth=("rzp_test_eEEzc0d8GHJgYL", "ZI7HtSUusg8kp6xU4DlFkHo5"))
    data = {
    "amount": total_price * 100,
    "currency": "INR",
    "receipt": "oid" }
    payment = client.order.create(data = data)
    print(payment)
    context ={}
    context['data'] = payment
    context['amount'] = payment["amount"]
    #emptying cart
    c.delete()
    #ordercompleted = True
    orders.update(is_completed = True)
    return render(req,"payment.html",context)

def insertProducts(req):
    if req.user.is_authenticated:
        user=req.user
        if req.method=="GET":
            form = AddProduct()
            return render(req,"insertProd.html",{'form':form})
        else:
            form =AddProduct(req.POST,req.FILES or None)
            if form.is_valid():
                form.save()
                messages.success(req,("Product Entered Successfully"))
                return redirect("/")
            else:
                
                messages.error(req,"Incorrect data")
                return render(req,"insertProd.html",{'form':form})
    else:
        return redirect("/login")