# coding=utf-8
from flask import Flask, request
app = Flask(__name__)

import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import hashlib
import ierror
import time
import json
import re
import pycurl
import StringIO
import certifi
import redis
import config


import xml.etree.cElementTree as ET
from bs4 import BeautifulSoup

import station_name_pro



class WechatCheck:
    def __init__(self):
        pass

    def getSHA1(self, token, timestamp, nonce):
        """用SHA1算法生成安全签名
        @param token:  票据
        @param timestamp: 时间戳
        @param encrypt: 密文
        @param nonce: 随机字符串
        @return: 安全签名
        """

        try:
            sortlist = [timestamp, nonce, token]
            sortlist.sort()
            sha = hashlib.sha1()
            sha.update("".join(sortlist))
            return [ierror.WXBizMsgCrypt_OK, sha.hexdigest()]
        except Exception, e:
            # print e
            return ierror.WXBizMsgCrypt_ComputeSignature_Error, None


class DataHandle:
    def xml_to_dict(self, xmltext):
        soup = BeautifulSoup(xmltext, features='xml')
        xml = soup.find('xml')
        data = dict([(item.name, item.text) for item in xml.find_all()])
        return data

    def dict_to_xml(self, data):
        xml = []
        for k in sorted(data.keys()):
            v = data.get(k)
            if k == 'detail' and not v.startswith('<![CDATA['):
                v = '<![CDATA[{}]]>'.format(v)
            xml.append('<{key}>{value}</{key}>'.format(key=k, value=v))
        return '<xml>{}</xml>'.format(''.join(xml))


class turingRobot:

    def __init__(self):
        self.requesturl = "http://www.tuling123.com/openapi/api"


    def curlpost(self, url, string=''):
        b = StringIO.StringIO()
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        head = ['Content-Type:application/json;charset=utf-8']
        c.setopt(pycurl.HTTPHEADER, head)
        c.setopt(pycurl.CUSTOMREQUEST, "POST")
        c.setopt(pycurl.POSTFIELDS, string)
        c.setopt(pycurl.WRITEFUNCTION, b.write)
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 5)
        c.perform()
        datas = b.getvalue()
        returndata = datas
        b.close()
        c.close()
        return returndata

    def query(self, info, userid, key="bbacbddd2b2349519b579cc0ff63de6e"):

        request_data = {
            "key": key,
            "info": info,
            "userid": userid
        }

        request_str = json.dumps(request_data)
        res = self.curlpost(self.requesturl, request_str)

        return json.loads(res)


@app.route('/', methods=["GET", "POST"])
def wechatcheck():
    signature = request.args.get("signature")
    echostr = request.args.get("echostr")
    timestamp = request.args.get("timestamp")
    nonce = request.args.get("nonce")

    if echostr != None:
        with open('test.txt', 'ab') as f:
            f.write(json.dumps([signature, echostr, timestamp, nonce]) + "\n")
            wcc = WechatCheck()
            res = wcc.getSHA1(config.token, timestamp, nonce)
            f.write(res[1] + "\n")

            if res[1] == signature:
                return echostr
            else:
                return None
    else:
        with open('test.txt', 'ab') as f:
            #------------------------------------
            xmls = str(request.get_data())+"\n"
            f.write(xmls)
            xmls = re.sub("\n", "", xmls)
            dh = DataHandle()
            wx_dict = dh.xml_to_dict(xmls)
            f.write(json.dumps(wx_dict))

            FromUserName = wx_dict['FromUserName']
            MsgId = wx_dict['MsgId']
            ToUserName = wx_dict['ToUserName']
            MsgType = wx_dict['MsgType']
            CreateTime = wx_dict['CreateTime']

            # ------------------------------------

            if MsgType == "text":
                Contents = wx_dict['Content']

                texttpl = '''
                <xml>
                    <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                    <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                    <CreateTime>%(CreateTime)s</CreateTime>
                    <MsgType><![CDATA[%(MsgType)s]]></MsgType>
                    <Content><![CDATA[%(Content)s]]></Content>
                    <MsgId>%(MsgId)s</MsgId>
                </xml>
                '''


                #key#########################

                redis_host = '101.200.190.17'
                redis_post = 6879
                redis_auth = '2514782544'
                r = redis.StrictRedis(host=redis_host, port=redis_post, password=redis_auth, db=1)

                wx_key = "wx_"+FromUserName

                if "火车票" in Contents:
                    args = Contents.split(" ")
                    if (len(args) == 4) and (args[0] == "火车票"):
                        sp = station_name_pro.stationInfo()
                        ###################################
                        allstr = sp._get_format_str(args[1], args[2], args[3])
                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": allstr,
                            "MsgId": MsgId
                        }

                        f.write(responese.encode("gbk"))
                        f.write(args[1])
                        f.write(args[2])
                        f.write(args[3])
                        return responese


                if r.get(wx_key):
                    tr = turingRobot()
                    content = tr.query(Contents, FromUserName, r.get(wx_key))
                    f.write(json.dumps(content))
                    txt = content["text"]
                    code = content["code"]

                    ##other##################################
                    if Contents == "*":
                        r.delete(wx_key)
                        txt = "连接记录已清除，请重新选择python机器人！"
                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": txt,
                            "MsgId": MsgId
                        }

                        return responese


                    #########################################
                    if code == 100000:
                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": txt,
                            "MsgId": MsgId
                        }

                        f.write(responese.encode("gbk"))
                        return responese

                    elif code == 200000:
                        url = content["url"]
                        text = content["text"]
                        link = "<a href='"+url+"'>"+text+"， 请点击链接查看！"+"</a>"
                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": link,
                            "MsgId": MsgId
                        }

                        f.write(responese.encode("gbk"))
                        return responese

                    elif code == 302000:
                        textimgTpl = '''
                        <xml>
                                <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                                <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                                <CreateTime>%(CreateTime)s</CreateTime>
                                <MsgType><![CDATA[%(MsgType)s]]></MsgType>
                                <ArticleCount>%(ArticleCount)d</ArticleCount>
                                <Articles>
                        '''
                        textimgTpl = textimgTpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": "news",
                            "ArticleCount": 8,
                        }

                        newslist = content["list"]
                        item = ""
                        ii = 1
                        for row in newslist:
                            if ii > 8:
                                break
                            tmp = '''
                                <item>
                                    <Title><![CDATA[%(Title)s]]></Title> 
                                    <Description><![CDATA[%(Description)s]]></Description>
                                    <PicUrl><![CDATA[%(PicUrl)s]]></PicUrl>
                                    <Url><![CDATA[%(Url)s]]></Url>
                                </item>
                            '''
                            tmp = tmp % {
                                "Title": row['article'],
                                "Description": row['source'],
                                "PicUrl": row['icon'],
                                "Url": row['detailurl'],
                            }

                            item += tmp
                            ii = ii + 1
                        textimgTpl += item
                        textimgTpl += '''
                            </Articles>
                          </xml>
                        '''
                        f.write(textimgTpl.encode("gbk"))
                        return textimgTpl
                    elif code == 308000:
                        textimgTpl = '''
                            <xml>
                                <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                                <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                                <CreateTime>%(CreateTime)s</CreateTime>
                                <MsgType><![CDATA[%(MsgType)s]]></MsgType>
                                <ArticleCount>%(ArticleCount)d</ArticleCount>
                                <Articles>
                            '''
                        textimgTpl = textimgTpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": "news",
                            "ArticleCount": 8,
                        }

                        newslist = content["list"]
                        item = ""
                        i = 1
                        for row in newslist:
                            if i > 8:
                                break
                            tmp = '''
                                <item>
                                    <Title><![CDATA[%(Title)s]]></Title> 
                                    <Description><![CDATA[%(Description)s]]></Description>
                                    <PicUrl><![CDATA[%(PicUrl)s]]></PicUrl>
                                    <Url><![CDATA[%(Url)s]]></Url>
                                </item>
                            '''
                            tmp = tmp % {
                                "Title": row['name'],
                                "Description": row['info'],
                                "PicUrl": row['icon'],
                                "Url": row['detailurl'],
                            }

                            item += tmp
                            i = i + 1
                        textimgTpl += item
                        textimgTpl += '''
                            </Articles>
                          </xml>
                        '''

                        f.write(textimgTpl.encode("gbk"))
                        return textimgTpl
                    elif code == 40001:
                        pass
                    elif code == 40002:
                        pass
                    elif code == 40004:
                        pass
                    elif code == 40007:
                        pass

                else:

                    if Contents in ["1", "2", "3"]:
                        r.set(wx_key, config.robot_key[int(Contents)-1])
                        r.expire(wx_key, config.robot_chat_time_len)
                        text = "你已选择和"+str(Contents)+"号python进行对话,请开始聊天！【聊天时间："+str(config.robot_chat_time_len)+"秒】"
                        #text = "you choose NO."+str(Contents)+" robot ,Please begin chat!"
                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": text,
                            "MsgId": MsgId
                        }

                        return responese
                    else:
                        #text = "Input 1/2/3 to choose different robot"
                        text = "请选择与下列型号进行对话：\n"
                        text += "对话1号python机器人 - 输入'1'\n"
                        text += "对话2号python机器人 - 输入'2'\n"
                        text += "对话3号python机器人 - 输入'3'\n"
                        text += "重选python机器人 - 输入'*'\n"

                        responese = texttpl % {
                            "ToUserName": FromUserName,
                            "FromUserName": ToUserName,
                            "CreateTime": CreateTime,
                            "MsgType": MsgType,
                            "Content": text,
                            "MsgId": MsgId
                        }

                        return responese

                #############################


            elif MsgType == "voice":
                pass
            elif MsgType == "video":
                pass
            elif MsgType == "shortvideo":
                pass
            elif MsgType == "location":
                pass
            elif MsgType == "link":
                pass
            elif MsgType == "image":
                imagetpl = '''
                <xml>
                    <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                    <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                    <CreateTime>%(CreateTime)s</CreateTime>
                    <MsgType><![CDATA[image]]></MsgType>
                    <Image><MediaId><![CDATA[%(MediaId)s]]></MediaId></Image>
                </xml>
                '''
                MediaId = wx_dict['MediaId']
                responese = imagetpl % {
                    "ToUserName": FromUserName,
                    "FromUserName": ToUserName,
                    "CreateTime": CreateTime,
                    "MediaId": MediaId
                }

                f.write(responese)
                return responese


    #


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        passwd = request.form['passwd']
        #username = request.args.get('username')
        #passwd = request.args.get('passwd')
        data = {
            "username": username,
            "passwd": passwd,
        }
        app.logger.debug(json.dumps(data))
        return json.dumps(data)




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)