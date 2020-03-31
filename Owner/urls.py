from django.urls import path, re_path

from Owner import views

urlpatterns =[
    path('test',views.test,name='test'),
    path('ownerlogin',views.login,name='login'),
    path('ownerregister',views.register,name='register'),
    path('sendmail',views.sendMessage,name='sendmail'),
    path('ownerindex',views.index,name='index'),
    path('ownerproductadd',views.addProdcut,name = 'addproduct'),
    path('ownerproductlist',views.productlist,name='productlist'),
    re_path('ownerproductchange/(?P<product_Id>\d+)/',views.productchange,name='productchange'),
    re_path('ownerproductdetail/(?P<product_Id>\d+)/',views.productdetail,name='productdetail'),
    path('ownerauthorization',views.authorization,name='authorization'),
    path('ownerauthorizationpage',views.authorizationpage,name='authorizationpage'),
    path('testcry',views.tsetcry,name='testcry'),
    path('uploadtest',views.uploadtest,name='uploadtest')
]