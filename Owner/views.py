import datetime
import hashlib
import os
import random
import json, time
import string
from threading import Thread
import ipfshttpclient
from django.core import serializers
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from Buyer.models import Msg
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
        session = request.session.get("nickname") #获取session
        user = Owner.objects.filter(username = cookie.get("username")).first()
        if user and user.nickname == session: #校验session
            return fun(request,*args,**kwargs)
        else:
            return HttpResponseRedirect('/owner/ownerlogin')
    return inner

def test(request):
    return HttpResponse('hello')

def getRandomData():
    result = str(random.randint(1000,9999))
    return result

def setPassword(password):
    md5 = hashlib.md5()
    md5.update(password.encode()) #python3加密针对字节
    result = md5.hexdigest()
    return result

def filter_addmsg(event_filter,eventmsg):
    while True:
        for event in event_filter.get_new_entries():
            eventmsg[0] = event.args._from
            eventmsg[1] = event.args._productId
            eventmsg[2] = event.args._msg

def filter_msg(event_filter,eventmsg):
    while True:
        for event in event_filter.get_new_entries():
            eventmsg[0] = event.args._from
            eventmsg[1] = event.args._msg

def login(request):
    result = {"error": ""}
    if request.method == "POST" and request.POST:
        login_valid = request.POST.get("login_valid")
        froms = request.COOKIES.get("from")
        if login_valid == "login_valid" and froms == "http://127.0.0.1:8000/owner/ownerlogin/":
            username = request.POST.get("username")
            user = Owner.objects.filter(username = username).first()
            if user:
                db_password = user.password
                password = setPassword(request.POST.get("password"))
                if db_password == password:
                    response = HttpResponseRedirect('/owner/ownerindex')
                    response.set_cookie("username",user.username)
                    response.set_cookie("id", user.id)
                    request.session["nickname"] = user.nickname #设置session
                    return response
                else:
                    result["error"] = "密码错误"
            else:
                result["error"] = "用户不存在"
        else:
             result["error"] = "请查询正确的接口进行登录"
    response = render(request,"ownerLogin.html",{"result": result})
    response.set_cookie("from","http://127.0.0.1:8000/owner/ownerlogin/")
    return response

def register(request):
    result = {"statu": "error","data":""}
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
                    owner = Owner()
                    owner.username = username
                    owner.email = username
                    owner.password = setPassword(userpass)
                    owner.address = w3.geth.personal.newAccount(setPassword(userpass))
                    owner.save()
                    result["statu"] = "success"
                    result["data"] = "恭喜！注册成功"
                    email.delete()
                    return HttpResponse("success")
            else:
                result["data"] = "验证码错误"
        else:
            result["data"] = "验证码不存在"
    return render(request, 'ownerRegister.html',locals())


def sendMessage(request):
    result = {"staue": "error","data":""}
    if request.method == "GET" and request.GET:
        recver = request.GET.get("email")
        try:
            subject = "注册成为区块链数字版权发布者"
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
    return render(request,'ownerIndex.html')

@cookieValid
def addProdcut(request):
    result = {"msg": ""}
    if request.method == "POST" and request.POST:
        # 获取前端表单数据
        postData = request.POST
        product_name = postData.get('product_name')
        product_category = postData.get('product_category')
        product_version = postData.get('product_version')
        product_status = postData.get('product_status')
        product_state = postData.get('product_state')
        product_show_time = datetime.datetime.now()
        product_price = postData.get('product_price')
        authorization = postData.get('authorization')
        if authorization =='True':
            authorization = 1
        else:
            authorization = 0
        product_prices = [int(Web3.toWei(i, 'ether')) for i in product_price.split(',')]
        id = request.COOKIES.get('id')

        #保存版权基本信息
        prodcut_files = request.FILES.getlist("prodcut_files")
        print(len(prodcut_files), len(product_prices))
        if len(prodcut_files) != len(prodcut_files):
            result['msg']='输入的价格与数量未成比例'
            return render(request,'ownerProductAddAndModify.html',context={'result':result})
        username = request.COOKIES.get('username')
        save_dir = "owner/files/{0}".format(username)
        temp_dir = "owner/files/temp"
        save_dir_path = os.path.join(MEDIA_ROOT, save_dir).replace("/", "\\")
        temp_dir_path = os.path.join(MEDIA_ROOT, temp_dir).replace("/", "\\")
        if not os.path.exists(save_dir_path):
            os.mkdir(save_dir_path)
        if os.path.exists(temp_dir_path):
            from shutil import rmtree
            rmtree(temp_dir_path)
        os.mkdir(temp_dir_path)
        tempdirlist = []
        for index, product in enumerate(prodcut_files):
            file_name = product.name
            file_path = "owner/files/%s/%s_%s_%s.%s" % (username,product_name,time.time(),index,'copyright')
            temp_path = "owner/files/temp/%s_%s_%s.%s" % (product_name,time.time(),index,'copyright')
            save_path = os.path.join(MEDIA_ROOT, file_path).replace("/", "\\")
            temp_save_path =  os.path.join(MEDIA_ROOT, temp_path).replace("/", "\\")
            tmpkey = random.sample(string.ascii_letters + string.digits, 16)
            tmpoffset = random.sample(string.ascii_letters + string.digits, 16)
            key = ''.join(tmpkey)
            offset = ''.join(tmpoffset)
            print(key,offset)
            pc = PrpCrypt(key,offset)
            pw1 = Password1()
            pw2 = Password2()
            pw1.password = key
            pw1.product_permit = index+1
            pw1.product_address = save_path
            pw2.password = offset
            pw2.product_permit = index+1
            pw2.product_address = save_path
            pw1.save()
            pw2.save()
            try:
                with open(save_path, "wb") as f:
                    for chunk in product.chunks(chunk_size=1024):
                        f.write(chunk)
                with open(save_path, 'rb') as file_object:
                    contents = file_object.read()
                    e = pc.encrypt(contents)
                with open(save_path, 'wb') as file_object:
                    file_object.write(e)
                with open(temp_save_path, 'wb') as file_object:
                    file_object.write(e)
                # 保存路径到数据库
            except Exception as e:
                print(e)
            p = Product()
            p.product_name = product_name
            p.product_version = product_version
            p.product_category = product_category
            p.product_status = product_status
            p.product_state = product_state
            p.product_price = product_prices[index]
            p.product_show_time = product_show_time
            p.product_address = save_path
            p.product_index = index
            p.product_key = setPassword(key)
            p.product_offset = setPassword(offset)
            p.product_suffix = file_name.rsplit(".", 1)[1]
            p.product_verify = int(authorization)
            tempdirlist.append(save_path)
            if id:
                p.owner = Owner.objects.get(id = int(id))
            else:
                return HttpResponseRedirect('owner/ownerlogin')
            p.save()

        #上传到ipfs
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001/http')
        ipfshash = client.add(temp_dir_path,recursive=True)
        ipfsdeschash = client.add_str(product_state)
        if os.path.exists(temp_dir_path):
            from shutil import rmtree
            rmtree(temp_dir_path)

        #上链
        owner = Owner.objects.get(id = int(id))
        w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        action = loadcontact(w3, 'cjs')
        block_filter = action.events.sendAddMsg.createFilter(fromBlock=0)
        eventmsg = [0,0,0]
        worker = Thread(target=filter_addmsg, args=(block_filter, eventmsg), daemon=True)
        worker.start()
        transactionHash = action.functions.addProductToStorage(product_name,product_category,product_version,ipfshash[-1]['Hash'],ipfsdeschash,bool(product_status),product_state,product_prices).transact({'from':Web3.toChecksumAddress(owner.address.lower())})
        transactiondetial = w3.eth.getTransaction(transactionHash)
        time.sleep(1)
        if((eventmsg[0]==owner.address)&(owner.address==transactiondetial['from'])&(eventmsg[2]==101)):
            result['msg'] = '恭喜，您的版权上链成功'
        elif((eventmsg[0]==owner.address)&(eventmsg[2]==100)):
            result['msg'] = '您的版权疑似和您之前发布的相同'
        elif(eventmsg[0]==0):
            result['msg'] = '系统繁忙，404'
        print(result['msg'],eventmsg)

        #ipfs及上链信息保存到数据库
        for index,tempdir in enumerate(tempdirlist):
            finalproducts = Product.objects.filter(product_address = tempdir)
            key = Password1.objects.filter(product_address = tempdir).first()
            offset = Password2.objects.filter(product_address = tempdir).first()
            key.product_bcId = eventmsg[1]
            offset.product_bcId = eventmsg[1]
            key.save()
            offset.save()
            for finalproduct in finalproducts:
                finalproduct.product_hashLink = ipfshash[index]['Hash']
                finalproduct.product_descLink = ipfsdeschash
                finalproduct.product_transactionHash = w3.toHex(transactionHash)
                finalproduct.product_bcId = eventmsg[1]
                finalproduct.product_blocknum = transactiondetial['blockNumber']
                finalproduct.product_timestamp = w3.eth.getBlock(transactiondetial['blockNumber'])['timestamp']
                finalproduct.save()
    context ={
        'result':result,
    }
    return render(request, "ownerProductAddAndModify.html",context=context)

@cookieValid
def productlist(request):
    # 链上查询发布版权
    result = {"msg": ""}
    id = request.COOKIES.get('id')
    owner = Owner.objects.get(id=int(id))
    w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
    action = loadcontact(w3, 'cjs')
    # productListNum =[]
    productListNum = action.functions.getProductIdStorageByAddress(Web3.toChecksumAddress(owner.address.lower())).call()
    if productListNum[0]==0:
        result['msg'] = '您还未发布版权，赶快去发布版权'
        context = {'result':result}
        return render(request, 'ownerProductList.html', context=context)
    product_List = [Product() for i in range(productListNum[0])]
    for index,product in enumerate(product_List):
        templist1 = action.functions.getProductStorageById_one(productListNum[index+1]).call()
        templist2 = action.functions.getProductStorageById_two(productListNum[index+1]).call()
        templist3 = action.functions.getPurchaseIdByProduceId(productListNum[index+1]).call()
        product.product_bcId = productListNum[index+1]
        product.product_name = templist1[0]
        product.product_category = templist1[1]
        product.product_version = templist1[2]
        product.product_hashLink = templist1[3]
        product.product_descLink = templist1[4]
        product.product_status = templist1[5]
        product.product_state = templist1[7]
        if(owner.address != templist1[6]): result['msg']='404,您的地址错误'
        product.product_blocknum = templist2[0]
        product.product_timestamp = templist2[1]
        product.product_transactionHash = str(w3.eth.getBlock(templist2[0])['transactions'])[11:-3]
        product.product_index = str(templist3[0])
    context ={
        'product_List':product_List,
        'result':result
    }
    return render(request,'ownerProductList.html',context=context)

@cookieValid
def productchange(request,product_Id):
    doType = True
    result = {"msg": ""}
    w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
    action = loadcontact(w3, 'cjs')
    templist = action.functions.getProductStorageById_one(int(product_Id)).call()
    result['msg'] ='您目前版权的状态是{0}'.format(templist[5])
    context = {'result': result,'doType':doType}
    if request.method == "POST" and request.POST:
        status = request.POST.get('status')
        productlist = Product.objects.filter(product_bcId=str(product_Id))
        id = request.COOKIES.get('id')
        if id:
            owner = Owner.objects.filter(id=int(id)).first()
        else:
            return HttpResponseRedirect('owner/ownerlogin')
        if(status =='TRUE'):
            statusbool = 1
        else:
            statusbool = 0
        for product in productlist:
            product.product_status = statusbool
            product.save()
        w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        action = loadcontact(w3, 'cjs')
        block_filter = action.events.sendMsg.createFilter(fromBlock=0)
        eventmsg = [0,0]
        worker = Thread(target=filter_msg, args=(block_filter, eventmsg), daemon=True)
        worker.start()
        # 留取hash值迭代版本使用
        transactionHash = action.functions.modifyProductToStorage(int(product_Id),bool(statusbool)).transact({'from':Web3.toChecksumAddress(owner.address.lower())})
        transactiondetial = w3.eth.getTransaction(transactionHash)
        time.sleep(1)
        # if((eventmsg[0]==owner.address)&(owner.address==transactiondetial['from'])&(eventmsg[1]==201)):
        #     result['msg'] = '成功'
        # elif((eventmsg[0]==owner.address)&((eventmsg[0]==0)|(eventmsg[1]==0))):
        #     result['msg'] = '恭喜，您的版权未修改成功'
        # print(result['msg'],eventmsg)
        return HttpResponseRedirect(reverse('owner:productlist'))
    return render(request,'ownerproductchange.html',context=context)

def productdetail(request,product_Id):
    product = Product.objects.filter(product_bcId=str(product_Id)).first()
    return render(request,'ownerProductDetail.html',context=locals())

@cookieValid
def authorization(request):
    page = request.GET.get('page')
    limit = request.GET.get('limit')
    id = request.COOKIES.get('id')
    msgs = Msg.objects.filter(owner_id= int(id)).filter(type=1)
    msg = msgs[(int(page) - 1) * int(limit):(int(page) - 1) * int(limit) + int(limit)]
    number = msgs.count()
    json_data = serializers.serialize('json', msg)
    json_data = json.loads(json_data)
    json_data_list = []
    for msgtemp, fields in zip(msg, json_data):
        add_msg = {'product_bcId': msgtemp.product.product_bcId,
                   'product_name': msgtemp.product.product_name,
                   'permisson': int(msgtemp.product.product_index) + 1,
                   'product_price': msgtemp.product.product_price,
                   'product_version': msgtemp.product.product_version,
                   'buyer_nickname' :msgtemp.buyer.nickname,
                   'buyer_email':msgtemp.buyer.email,
                   'msg_id': msgtemp.id,
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
def authorizationpage(request):
    return render(request,'ownerauthorizationPage.html')


def tsetcry(request):
    if request.method == "POST" and request.POST:
        # product_name = request.POST.get('')
        # print(product_name[0],product_name[1],product_name[2],product_name[3])
        # print(product_name)
        test = request.POST.get('test')
        imgs = request.FILES.getlist("file")
        print(imgs)
        # 保存图片
        for index, img in enumerate(imgs):
            # 保存图片到服务器
            file_name = img.name
            print(index,file_name)
            file_path = "owner/files/%s_%s.%s" % (file_name, index, file_name.rsplit(".", 1)[1])
            save_path = os.path.join(MEDIA_ROOT, file_path).replace("/", "\\")
            # pc = PrpCrypt('keyskeyskeyskeys','keyskeyskeyskeys')
            try:
                with open(save_path, "wb") as f:
                    for chunk in img.chunks(chunk_size=1024):
                        f.write(chunk)
                # with open(save_path, 'rb') as file_object:
                #     contents = file_object.read()
                #     e = pc.encrypt(contents)
                # with open(save_path, 'wb') as file_object:
                #     d = pc.decrypt(e)
                #     file_object.write(d)
            except Exception as e:
                print(e)
        return HttpResponse(0)
    return render(request,'testcry.html')


def uploadtest(request):
    if request.method == "POST" and request.POST:
        # product_name = request.POST.get('')
        # print(product_name[0],product_name[1],product_name[2],product_name[3])
        # print(product_name)
        email = request.POST.get('email')
        print(email)
        imgs = request.FILES.getlist("prodcut_files")
        print(imgs,email)
        # 保存图片
        for index, img in enumerate(imgs):
            # 保存图片到服务器
            file_name = img.name
            print(index,file_name)
            file_path = "owner/files/%s_%s.%s" % (file_name, index, file_name.rsplit(".", 1)[1])
            save_path = os.path.join(MEDIA_ROOT, file_path).replace("/", "\\")
            # pc = PrpCrypt('keyskeyskeyskeys','keyskeyskeyskeys')
            try:
                with open(save_path, "wb") as f:
                    for chunk in img.chunks(chunk_size=1024):
                        f.write(chunk)
                # with open(save_path, 'rb') as file_object:
                #     contents = file_object.read()
                #     e = pc.encrypt(contents)
                # with open(save_path, 'wb') as file_object:
                #     d = pc.decrypt(e)
                #     file_object.write(d)
            except Exception as e:
                print(e)
        return HttpResponse('hello')
    return render(request,'testupload.html')