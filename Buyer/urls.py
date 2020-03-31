from django.urls import path, re_path

from Buyer import views

urlpatterns= [
    path('buyerregister',views.register,name ='register'),
    path('buyerlogin',views.login,name='login'),
    path('sendmail',views.sendMessage,name='sendmail'),
    path('buyerindex',views.index,name='index'),
    path('buyerproductlist',views.productlist,name='productlist'),
    path('productlistvisual',views.productlistvisual,name='productlistvisual'),
    path('productfuzzysearch',views.productfuzzysearch,name= 'productfuzzysearch'),
    path('buyerproductdetail',views.buyerproductdetail,name='productdetail'),
    path('buyeraddproduct',views.buyeraddproduct,name='addproduct'),
    path('buyershoppingcar',views.shoppingcar,name='shoppingcar'),
    path('buyershoppingcarlist',views.shoppingcarlist,name='shoppingcarlist'),
    path('shoppingcarfuzzysearch',views.shoppingcarfuzzysearch,name='shoppingcarfuzzysearch'),
    path('buyershoppingdetail',views.shoppingdetail,name='shoppingdetail'),
    path('buyerpurchase',views.purchase,name='buyerpurchase'),
    path('mypurchaseproduct',views.mypurchaseproduct,name='mypurchaseproduct'),
    path('mypurchaseproductlist',views.mypurchaseproductlist,name='mypurchaseproductlist'),
    path('mypurchaseproductfuzzysearch',views.mypurchaseproductfuzzysearch,name='mypurchaseproductfuzzysearch'),
    re_path('buyerproductdownload/(?P<product_Id>\d+)/(?P<permission>\d+)/',views.productdownload,name='productdownload'),
    re_path('buyerproductsecret/(?P<product_Id>\d+)/(?P<permission>\d+)/',views.productsecret,name='productsecret'),
    path('test',views.test,name='test')
]