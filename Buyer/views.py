import datetime
import hashlib
import os
import random
import json, time
from tempfile import TemporaryFile, NamedTemporaryFile
from threading import Thread
from wsgiref.util import FileWrapper

import ipfshttpclient
from django.core import serializers
from django.core.mail import EmailMultiAlternatives
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, FileResponse
from django.shortcuts import render
from django.urls import reverse

from Buyer.models import Buyer, Msg, Purchase, PurchaseMessage
from Owner.models import Owner, EmailValid, PrpCrypt, Product, Password1, Password2
from web3 import Web3
from drmtest.settings import MEDIA_ROOT

def loadcontact(w3, contract):
    fn_abi = 'F:\\onedrive\\blockchain\\code\\final\\demo\\{0}.abi'.format(contract)
    fn_addr = 'F:\\onedrive\\blockchain\\code\\final\\demo\\{0}.addr'.format(contract)

    with open(fn_abi) as f:
        abi = json.load(f)

    with open(fn_addr) as f:
        addr = f.read()
        addr = Web3.toChecksumAddress(addr.lower())

    return w3.eth.contract(address=addr, abi=abi)

def cookieValid(fun):
    def inner(request,*args,**kwargs):
        cookie = request.COOKIES
        session = request.session.get("buyernickname") #获取session
        user = Buyer.objects.filter(id = cookie.get("buyerid")).first()
        if user and user.nickname == session: #校验session
            return fun(request,*args,**kwargs)
        else:
            return HttpResponseRedirect('/buyer/buyerlogin')
    return inner

def getRandomData():
    result = str(random.randint(1000,9999))
    return result

def setPassword(password):
    md5 = hashlib.md5()
    md5.update(password.encode()) #python3加密针对字节
    result = md5.hexdigest()
    return result

def filter_msg(event_filter,eventmsg):
    while True:
        for event in event_filter.get_new_entries():
            eventmsg[0] = event.args._from
            eventmsg[1] = event.args._msg

def filter_purchasemsg(event_filter,eventmsg):
    while True:
        for event in event_filter.get_new_entries():
            eventmsg[0] = event.args._from
            eventmsg[1] = event.args._purchaseId
            eventmsg[2] = event.args._msg

def login(request):
    result = {"error": ""}
    if request.method == "POST" and request.POST:
        login_valid = request.POST.get("login_valid")
        froms = request.COOKIES.get("buyerfrom")
        if login_valid == "login_valid" and froms == "http://127.0.0.1:8000/buyer/buyerlogin/":
            username = request.POST.get("username")
            user = Buyer.objects.filter(username = username).first()
            if user:
                db_password = user.password
                password = setPassword(request.POST.get("password"))
                if db_password == password:
                    response = HttpResponseRedirect('/buyer/buyerindex')
                    response.set_cookie("buyerusername",user.username)
                    response.set_cookie("buyerid", user.id)
                    request.session["buyernickname"] = user.nickname #设置session
                    return response
                else:
                    result["error"] = "密码错误"
            else:
                result["error"] = "用户不存在"
        else:
             result["error"] = "请查询正确的接口进行登录"
    response = render(request,"buyerLogin.html",{"result": result})
    response.set_cookie("buyerfrom","http://127.0.0.1:8000/buyer/buyerlogin/")
    return response

def register(request):
    result = {"status": "error","data":""}
    w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
    if request.method == "POST" and request.POST:
        username = request.POST.get("username")
        code = request.POST.get("code")
        userpass = request.POST.get("userpass")
        email = EmailValid.objects.filter(email_address = username).last()
        if email:
            if code == email.value:
                now = time.mktime(
                    datetime.datetime.now().timetuple()
                )
                db_now = time.mktime(email.times.timetuple())
                if now - db_now >= 86400:
                    result["data"] = "验证码过期"
                    email.delete()
                else:
                    buyer = Buyer()
                    buyer.username = username
                    buyer.email = username
                    buyer.password = setPassword(userpass)
                    buyer.address = w3.geth.personal.newAccount(setPassword(userpass))
                    buyer.save()
                    result["statu"] = "success"
                    result["data"] = "恭喜！注册成功"
                    email.delete()
                    return HttpResponseRedirect(reverse('buyer:login'))
            else:
                result["data"] = "验证码错误"
        else:
            result["data"] = "验证码不存在"
    return render(request, 'buyerRegister.html',locals())

def sendMessage(request):
    result = {"staue": "error","data":""}
    if request.method == "GET" and request.GET:
        recver = request.GET.get("email")
        try:
            subject = "注册成为区块链数字版权购买者"
            text_content = "hello new user"
            value = getRandomData()
            html_content = """
            <div>
                <p>
                    尊敬的用户，您的用户验证码是:%s,请不要告诉任何人哦。
                </p>
            </div>
            """%value
            message = EmailMultiAlternatives(subject,text_content,"gin_yz@163.com",[recver])
            message.attach_alternative(html_content,"text/html")
            message.send()
        except Exception as e:
            result["data"] = str(e)
        else:
            result["staue"] = "success"
            result["data"] = "success"
            email = EmailValid()
            email.value = value
            email.times = datetime.datetime.now()
            email.email_address = recver
            email.save()
        finally:
            return JsonResponse(result)

@cookieValid
def index(request):
    return render(request,'buyerIndex.html')

@cookieValid
def productlist(request):

    return render(request,'buyerProductList.html')



def test(request):
    return render(request,'test.html')

@cookieValid
def productlistvisual(request):
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    print(page,limit)
    productraws = Product.objects.filter(product_status=1)
    products = productraws[(int(page)-1)*int(limit):(int(page)-1)*int(limit)+int(limit)]
    number = productraws.count()
    json_data = serializers.serialize('json', products)
    json_data = json.loads(json_data)
    print(number)
    json_data_list =[]
    for fields in json_data:
        json_data_list.append(fields.get('fields'))
    json_data_return ={
        "code": 0,
        "msg": "",
        "count": number,
        "data":json_data_list
    }
    return JsonResponse(json_data_return, safe=False)

@cookieValid
def buyerproductdetail(request):
    hash = request.GET.get('hash')
    products = Product.objects.filter(product_hashLink=hash)
    product =products.first()
    context ={
        'product':product,
    }
    return render(request,'buyerProductDetail.html',context=context)

@cookieValid
def buyeraddproduct(request):
    if request.POST and request.method == 'POST':
        desc =  request.POST.get('desc')
        product_id = request.POST.get('product_Id')
        w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        action = loadcontact(w3, 'cjs')
        product = Product.objects.filter(id=int(product_id)).first()
        msg = Msg()
        msg.msg = desc
        msg.buyer = Buyer.objects.filter(id=int(request.COOKIES.get('buyerid'))).first()
        msg.product = product
        msg.owner = product.owner
        msg.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # 1为需要验证
        if product.product_verify ==1:
            msg.type = 1
            msg.save()
            # gas :32542   gasprice:不固定,一般为20000000000 交易价格虚拟机上固定:0.00065084ETH  hash留作备份
            transactionHash = action.functions.purchase(int(product.product_bcId),int(product.product_index) +1 ).transact({'from':Web3.toChecksumAddress(msg.buyer.address.lower()),'value':int(product.product_price)})
        # 无需验证，直接购买，下载前可以退款
        else:
            msg.type = 0
            msg.save()
            transactionHash1 = action.functions.purchase(int(product.product_bcId),int(product.product_index) + 1).transact({'from': Web3.toChecksumAddress(msg.buyer.address.lower()),'value': int(product.product_price)})
    return HttpResponse('hello')

@cookieValid
def shoppingcar(request):
    return render(request,'shoppingCar.html')

@cookieValid
def shoppingcarlist(request):
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    id = request.COOKIES.get('buyerid')
    # type 0能下载但未下载  1 还未审核 2已经下载
    msgraws = Msg.objects.filter(Q(type= 1 )|Q(type = 0)).filter(buyer_id = int(id))
    # print(msgraws.first().id)
    msgs = msgraws[(int(page)-1)*int(limit):(int(page)-1)*int(limit)+int(limit)]
    number = msgraws.count()
    json_data = serializers.serialize('json', msgs)
    json_data = json.loads(json_data)
    json_data_list =[]
    for msg,fields in zip(msgs,json_data):
        add_msg = {'product_bcId':msg.product.product_bcId,
                   'product_name':msg.product.product_name,
                   'product_state':msg.product.product_state,
                   'product_price':msg.product.product_price,
                   'product_hashLink':msg.product.product_hashLink,
                   'time':msg.time,
                   'msg_id':msg.id
                   }
        if msg.type==0:
            fields.get('fields')['type'] = '还未下载，可退款'
        else:
            fields.get('fields')['type'] = '版权发布者还未授权'
        json_data_list.append(dict(fields.get('fields'),**add_msg))
    json_data_return ={
        "code": 0,
        "msg": "",
        "count": number,
        "data":json_data_list
    }
    return JsonResponse(json_data_return, safe=False,json_dumps_params={'ensure_ascii':False})

@cookieValid
def shoppingdetail(request):
    hash = request.GET.get('hash')
    msg_id  =request.GET.get('msg_id')
    products = Product.objects.filter(product_hashLink=hash)
    msg = Msg.objects.filter(id = int(msg_id)).first()
    product =products.first()
    context ={
        'product':product,
        'msg':msg
    }
    return render(request,'buyerShoppingDetail.html',context=context)


def purchase(request):
    result ={'msg':''}
    if request.POST and request.method == 'POST':
        w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        action = loadcontact(w3, 'cjs')
        act = request.POST.get('action')
        msg_id = request.POST.get('msg_id')
        msg = Msg.objects.filter(id = int(msg_id)).first()
        block_filter = action.events.sendPurchaseMsg.createFilter(fromBlock=0)
        # type 0能下载但未下载  1 还未审核 2 交易成功
        if msg.type == 0 and act == 'purchase':
            eventmsg = [0, 0, 0]
            worker = Thread(target=filter_purchasemsg, args=(block_filter, eventmsg), daemon=True)
            worker.start()
            transactionHash = action.functions.controlPurchaseByPython(Web3.toChecksumAddress(msg.owner.address.lower()),int(msg.product.product_bcId),int(msg.product.product_index)+1,int(msg.product.product_price),600).transact({'from': Web3.toChecksumAddress(msg.buyer.address.lower())})
            transactiondetial = w3.eth.getTransaction(transactionHash)
            time.sleep(1)
            print(eventmsg)
            print(transactiondetial['from'],msg.buyer.address)
        if (eventmsg[0]==msg.buyer.address)&(msg.buyer.address==transactiondetial['from'])&(eventmsg[2] == 600):
            result['msg']='购买成功，钱已转账，不能退款'
            msg.type = 2
            msg.save()
            purchasemsg = PurchaseMessage()
            purchasemsg.product = msg.product
            purchasemsg.permission = str(msg.product.product_index+1)
            purchasemsg.buyer = msg.buyer
            purchasemsg.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            purchasemsg.purchaseId = int(eventmsg[1])
            purchasemsg.blocknum = transactiondetial['blockNumber']
            purchasemsg.transactionHash = w3.toHex(transactionHash)
            purchasemsg.blocknum = transactiondetial['blockNumber']
            purchasemsg.timestamp = w3.eth.getBlock(transactiondetial['blockNumber'])['timestamp']
            purchasemsg.save()
        if act == 'repeal':
            eventmsg = [0, 0]
            worker = Thread(target=filter_msg, args=(block_filter, eventmsg), daemon=True)
            worker.start()
            transaction = action.functions.controlPurchaseByPython(Web3.toChecksumAddress(msg.buyer.address.lower()),int(msg.product.product_bcId),int(msg.product.product_index)+1,int(msg.product.product_price),700).transact({'from': Web3.toChecksumAddress(msg.buyer.address.lower())})
            time.sleep(1)
            if eventmsg[1] == 700:
                time.sleep(1)
                result['msg']='撤回成功，钱已到账，手续费已扣'
                msg.delete()
        if msg.type == 1:
            result['msg']='版权发布者还未授权，请耐心等待'
        context ={
            'result':result,
        }
    return render(request,'purchaseResult.html',context=context)

@cookieValid
def mypurchaseproduct(request):
    # # 链上查询购买版权
    # result = {"msg": ""}
    # id = request.COOKIES.get('buyerid')
    # buyer = Buyer.objects.get(id=int(id))
    # w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
    # action = loadcontact(w3, 'cjs')
    # purchaseListNum = action.functions.getPurchaseIdStorageByAddress(Web3.toChecksumAddress(buyer.address.lower())).call()
    # print(purchaseListNum)
    # if purchaseListNum[0]==0:
    #     result['msg'] = '您还未购买版权，赶快去购买版权'
    #     context = {'result':result}
    #     return render(request, 'mypurchaseproduct.html', context=context)
    # purchase_List = [Purchase() for i in range(purchaseListNum[0])]
    # for index,purchase in enumerate(purchase_List):
    #     templist = action.functions.getPurchaseStorageById(purchaseListNum[index+1]).call()
    #     templist1 = action.functions.getProductStorageById_one(int(templist[0])).call()
    #     print(templist,templist1)
    #     print(index)
    #     purchase.purchaseId = purchaseListNum[index+1]
    #     purchase.product_bcId = templist[0]
    #     purchase.blocknum = templist[1]
    #     purchase.timestamp = templist[2]
    #     purchase.permission = templist[3]
    #     purchase.product_name = templist1[0]
    #     purchase.product_category = templist1[1]
    #     purchase.product_version = templist1[2]
    #     purchase.product_hashLink = templist1[3]
    #     purchase.product_descLink = templist1[4]
    #     purchase.product_status = templist1[5]
    #     purchase.product_state = templist1[7]
    #     if(buyer.address != templist[4]): result['msg']='404,您的地址错误'
    # context ={
    #     'purchase_List':purchase_List,
    #     'result':result
    # }
    # return render(request,'mypurchaseproduct.html',context=context)
    return render(request,'mypurchaseproduct.html')

@cookieValid
def mypurchaseproductlist(request):
    result = []
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    id = request.COOKIES.get('buyerid')
    buyer = Buyer.objects.get(id=int(id))
    w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
    action = loadcontact(w3, 'cjs')
    purchaseListNum = action.functions.getPurchaseIdStorageByAddress(Web3.toChecksumAddress(buyer.address.lower())).call()
    print(purchaseListNum)
    for index in range(purchaseListNum[0]):
        templist = action.functions.getPurchaseStorageById(purchaseListNum[index+1]).call()
        # print(templist,templist1)
        # print(index)
        # purchase.purchaseId = purchaseListNum[index+1]
        # purchase.product_bcId = templist[0]
        # purchase.blocknum = templist[1]
        # purchase.timestamp = templist[2]
        # purchase.permission = templist[3]
        # purchase.product_name = templist1[0]
        # purchase.product_category = templist1[1]
        # purchase.product_version = templist1[2]
        # purchase.product_hashLink = templist1[3]
        # purchase.product_descLink = templist1[4]
        # purchase.product_status = templist1[5]
        # purchase.product_state = templist1[7]
        # 与链上检查是否一致
        purchasemsg = PurchaseMessage.objects.filter(purchaseId= purchaseListNum[index+1]).last()
        print(templist[4],purchaseListNum[index+1])
        if purchasemsg.buyer.address != templist[4] : result.append('addresserror')
        if int(purchasemsg.product.product_bcId) != templist[0] : result.append('bciderror')
        if purchasemsg.blocknum != templist[1]: result.append('blocknumerror')
        if purchasemsg.timestamp != templist[2] : result.append('timestamperror')
        if int(purchasemsg.permission) != templist[3]:result.append('permisson')
        print(result)
        context = {
            'result':result,
        }
        #等下写error
        if result: return render(request,'error.html',context=context)
    purchasemsgs = PurchaseMessage.objects.filter(buyer_id= int(id))
    msgs = purchasemsgs[(int(page) - 1) * int(limit):(int(page) - 1) * int(limit) + int(limit)]
    number = purchasemsgs.count()
    json_data = serializers.serialize('json', msgs)
    json_data = json.loads(json_data)
    json_data_list = []
    for msg, fields in zip(msgs, json_data):
        add_msg = {'product_bcId': msg.product.product_bcId,
                   'product_name': msg.product.product_name,
                   'product_version': msg.product.product_version,
                   }
        json_data_list.append(dict(fields.get('fields'), **add_msg))
    json_data_return = {
        "code": 0,
        "msg": "",
        "count": number,
        "data": json_data_list
    }
    return JsonResponse(json_data_return, safe=False, json_dumps_params={'ensure_ascii': False})

@cookieValid
def mypurchaseproductfuzzysearch(request):
    result = []
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    search = request.GET.get('search')
    id = request.COOKIES.get('buyerid')
    buyer = Buyer.objects.get(id=int(id))
    w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
    action = loadcontact(w3, 'cjs')
    purchaseListNum = action.functions.getPurchaseIdStorageByAddress(
        Web3.toChecksumAddress(buyer.address.lower())).call()
    # print(purchaseListNum)

    for index in range(purchaseListNum[0]):
        templist = action.functions.getPurchaseStorageById(purchaseListNum[index + 1]).call()
        # 与链上检查是否一致
        purchasemsg = PurchaseMessage.objects.filter(purchaseId=purchaseListNum[index + 1]).first()
        if purchasemsg.buyer.address != templist[4]: result.append('addresserror')
        if int(purchasemsg.product.product_bcId) != templist[0]: result.append('bciderror')
        if purchasemsg.blocknum != templist[1]: result.append('blocknumerror')
        if purchasemsg.timestamp != templist[2]: result.append('timestamperror')
        if int(purchasemsg.permission) != templist[3]: result.append('permisson')
        context = {
            'result': result,
        }
        # 等下写error
        if result: return render(request, 'error.html', context=context)

    purchasemsgs = PurchaseMessage.objects.filter(buyer_id=int(id)).filter(Q(product__product_name__icontains=str(search)) | Q(product__product_state__icontains=str(search)) | Q(time__icontains= str(search)))
    msgs = purchasemsgs[(int(page) - 1) * int(limit):(int(page) - 1) * int(limit) + int(limit)]
    number = purchasemsgs.count()
    json_data = serializers.serialize('json', msgs)
    json_data = json.loads(json_data)
    json_data_list = []
    for msg, fields in zip(msgs, json_data):
        add_msg = {'product_bcId': msg.product.product_bcId,
                   'product_name': msg.product.product_name,
                   'product_version': msg.product.product_version,
                   }
        json_data_list.append(dict(fields.get('fields'), **add_msg))
    json_data_return = {
        "code": 0,
        "msg": "",
        "count": number,
        "data": json_data_list
    }
    return JsonResponse(json_data_return, safe=False, json_dumps_params={'ensure_ascii': False})

@cookieValid
def productdownload(request,product_Id,permission):
    id = request.COOKIES.get('buyerid')
    product = Product.objects.filter(product_bcId=int(product_Id)).filter(product_index= int(permission)-1).first()
    save_dir_path = product.product_address.replace("/", "\\")
    # key = Password1.objects.filter(product_Id = int(product_Id)).filter(product_permit = int(permission)).first()
    # offset = Password2.objects.filter(product_Id = int(product_Id)).filter(product_permit = int(permission)).first()
    file = open(save_dir_path,'rb')
    response = FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']='attachment;filename=%s_%s_%d.%s' % (product.product_name,product.product_version,product.product_index+1,product.product_suffix)
    return response

@cookieValid
def productsecret(request,product_Id,permission):
    id = request.COOKIES.get('buyerid')
    # product = Product.objects.filter(product_bcId=int(product_Id)).filter(product_index= int(permission)-1).first()
    # 之后再写，查询链上，只有买了的才能下载
    key = Password1.objects.filter(product_bcId = int(product_Id)).filter(product_permit = int(permission)).first()
    offset = Password2.objects.filter(product_bcId = int(product_Id)).filter(product_permit = int(permission)).first()
    # licence = TemporaryFile(delete=False)
    # print(licence.name)
    # licence.write(('%s%s' % (key.password,offset.password)).encode())
    # response = FileResponse(licence)
    # response['Content-Type'] = 'application/octet-stream'
    # response['Content-Disposition'] = 'attachment;filename=%s_%s_%d.%s' % (product.product_name, product.product_version, product.product_index + 1, 'licence')
    # return response
    return HttpResponse('%s%s' % (key.password,offset.password))

@cookieValid
def productfuzzysearch(request):
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    search = request.GET.get('search')
    print(page,limit,search)
    productraws = Product.objects.filter(product_status=1).filter(Q(product_name__icontains=str(search)) | Q(product_state__icontains= str(search)))
    products = productraws[(int(page)-1)*int(limit):(int(page)-1)*int(limit)+int(limit)]
    number = productraws.count()
    json_data = serializers.serialize('json', products)
    json_data = json.loads(json_data)
    print(number)
    json_data_list =[]
    for fields in json_data:
        json_data_list.append(fields.get('fields'))
    json_data_return ={
        "code": 0,
        "msg": "",
        "count": number,
        "data":json_data_list
    }
    return JsonResponse(json_data_return, safe=False)

@cookieValid
def shoppingcarfuzzysearch(request):
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    id = request.COOKIES.get('buyerid')
    search = request.GET.get('search')
    # type 0能下载但未下载  1 还未审核 2已经下载
    msgraws = Msg.objects.filter(Q(type=1) | Q(type=0)).filter(buyer_id=int(id)).filter(Q(product_name__icontains=str(search)) | Q(product_state__icontains= str(search)))
    # print(msgraws.first().id)
    msgs = msgraws[(int(page) - 1) * int(limit):(int(page) - 1) * int(limit) + int(limit)]
    number = msgraws.count()
    json_data = serializers.serialize('json', msgs)
    json_data = json.loads(json_data)
    json_data_list = []
    for msg, fields in zip(msgs, json_data):
        add_msg = {'product_bcId': msg.product.product_bcId,
                   'product_name': msg.product.product_name,
                   'product_state': msg.product.product_state,
                   'product_price': msg.product.product_price,
                   'product_hashLink': msg.product.product_hashLink,
                   'time': msg.time,
                   'msg_id': msg.id
                   }
        if msg.type == 0:
            fields.get('fields')['type'] = '还未下载，可退款'
        else:
            fields.get('fields')['type'] = '版权发布者还未授权'
        json_data_list.append(dict(fields.get('fields'), **add_msg))
    json_data_return = {
        "code": 0,
        "msg": "",
        "count": number,
        "data": json_data_list
    }
    return JsonResponse(json_data_return, safe=False, json_dumps_params={'ensure_ascii': False})


