# coding=utf-8
import requests
from lxml.html import etree
import sys
import json
import time
import re
import os
import traceback
import tkinter as tk

from tkinter import messagebox


class weibo(object):
    def __init__(self, bid: str, weibo_url: str, user_id: str, user_name: str, content: str, public_time: str,
                 public_timestamp: int, share_scope: str, like_num: int, forward_num: int, comment_num: int,
                 comment_list: list, is_original: int, r_href: str, links: list, img_list: list, video_url: str,
                 weibo_from: str, article_url: str, article_content: str, remark: str, r_weibo: dict):
        """

        :param bid: 微博bid
        :param weibo_url: 微博链接
        :param user_id: 用户id
        :param user_name: 用户名
        :param content: 微博正文
        :param public_time: 发表时间
        :param public_timestamp: 发表时间戳
        :param share_scope: 可见范围
        :param like_num: 点赞数
        :param forward_num: 转发数
        :param comment_num: 评论数
        :param comment_list: 评论列表
        :param is_original: 是否为原创，原创为1，转发为0，快转为-1
        :param r_href: 原微博url
        :param links: 微博正文中包含的链接
        :param img_list: 图片链接列表
        :param video_url: 视频链接
        :param weibo_from: 微博来源
        :param article_url: 文章链接
        :param article_content: 文章内容
        :param remark: 备注
        :param r_weibo: 源微博
        """
        self.bid = bid
        self.weibo_url = weibo_url
        self.user_id = user_id
        self.user_name = user_name
        self.content = content
        self.public_time = public_time
        self.public_timestamp = public_timestamp
        self.share_scope = share_scope
        self.like_num = like_num
        self.forward_num = forward_num
        self.comment_num = comment_num
        self.comment_list = comment_list
        self.is_original = is_original
        self.r_href = r_href
        self.links = links
        self.img_list = img_list
        self.video_url = video_url
        self.weibo_from = weibo_from
        self.article_url = article_url
        self.article_content = article_content
        self.remark = remark
        self.r_weibo = r_weibo

    def to_dict_with_simple_r_weibo(self):
        if self.r_weibo:
            simple_r_weibo_info = {
                "user_name": self.r_weibo["user_name"],
                "content": self.r_weibo["content"],
                "weibo_url": self.r_weibo["weibo_url"],
                "bid": self.r_weibo["bid"]
            }
        else:
            simple_r_weibo_info = self.r_weibo
        weibo_dict = {
            "bid": self.bid,
            "weibo_url": self.weibo_url,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "content": self.content,
            "public_time": self.public_time,
            "public_timestamp": self.public_timestamp,
            "share_scope": self.share_scope,
            "like_num": self.like_num,
            "forward_num": self.forward_num,
            "comment_num": self.comment_num,
            "comment_list": self.comment_list,
            "links": self.links,
            "img_list": self.img_list,
            "article_url": self.article_url,
            "article_content": self.article_content,
            "video_url": self.video_url,
            "weibo_from": self.weibo_from,
            "is_original": self.is_original,
            "r_href": self.r_href,
            "remark": self.remark,
            "r_weibo": simple_r_weibo_info
        }
        return weibo_dict

    # 没时间了，以后写
    def to_sql(self):
        pass

    def to_string(self):
        pass

    def to_list(self):
        pass

    def get_fields(self):
        pass


class WeiboTool(object):
    def __init__(self):
        self.r_weibo_list = []
        pass

    def get_null_weibo(self):
        null_weibo = weibo("", "", "", "", "", "", 0, "", 0, 0, 0, [], 1, "", [], [], "", "", "", "", "", {})
        return null_weibo

    def get_weibo_div(self, session, url):
        # 对单条微博的链接发起请求，解析出div[@tbinfo]
        # 链接格式为 https://weibo.com/xxxxxxx/xxxxxxx 例：https://weibo.com/5762457113/K058KnPJb
        weibo_div = ""
        count = 0
        while True:
            count += 1
            if count % 3 == 0:
                time.sleep(3)
            if count == 6:
                print("该条无法获取，请确认该条微博是否可见，链接 {}".format(url))
                return {}
            text = session.get(url).text
            weibo_page_parse = etree.HTML(text)
            scripts = weibo_page_parse.xpath("/html/script")
            weibo_parse = ""
            # 找到正文内容的script
            for script in scripts[-1::-1]:
                script_str = etree.tostring(script, encoding="utf-8").decode("utf-8")
                if "feed_list_content" in script_str:
                    # 提取出值中的json
                    tmp_json = json.loads(re.search(r"\(({.*})\)", script_str).group(1), encoding="utf-8")
                    # 获取html。符号编码不知道哪出问题了，手动替换
                    weibo_html = tmp_json["html"].replace("&lt;", "<").replace("&gt;", ">")
                    weibo_parse = etree.HTML(weibo_html)
                    break

            try:
                # 成功了就退出for循环
                weibo_div = weibo_parse.xpath("//div[@tbinfo]")[0]
            except:
                # 失败就下一个while
                continue

            break

        return weibo_div

    def parse_weibo_from_forward_div(self, session, forward_div):
        """
        部分微博的在转发页可以看到，但原链接已经无法打开，则在这里进行解析
        会缺失一些数据，但总之尽量弄到
        这个方法是parse_weibo_from_div的变体，如果是在看代码的话，建议先看parse_weibo_from_div
        :param session: requests.session()
        :param forward_div: 微博中转发的部分 //div[@tbinfo]//div[@class='WB_feed_expand']
        :return:
        """
        # weibo_div = self.get_weibo_div(session, url)
        # r_weibo_div = weibo_div.xpath("//div[@class='WB_feed_expand']")[0]
        remark = ""
        remark += "该条微博信息由转发页解析出来，原微博链无法加载"
        parse = forward_div

        count = 0
        # 微博链接
        while True:
            if count > 10:
                print("调用parse_weibo_from_div的参数有误，返回空weibo对象")
                time.sleep(3)
                return self.get_null_weibo()
            count += 1
            try:
                weibo_url = "https://weibo.com" + parse.xpath("//div[contains(@class,'WB_from')]/a/@href")[0]
                break
            except:
                pass
        if config["print_level"]:
            print("开始解析链接 {}".format(weibo_url))

        # 用户id和bid
        bid_ele = parse.xpath(".//a[@node-type='feed_list_item_date']/@href")
        userid_and_bid_re = re.search("/(\d+)/(\w+)", bid_ele[0])
        user_id = userid_and_bid_re.group(1)
        bid = userid_and_bid_re.group(2)
        # 用户名
        user_name = parse.xpath(".//div/a[@class='W_fb S_txt1']/text()")[0]

        # 正文
        content_ele = parse.xpath(
            ".//div[@node-type='feed_list_forwardContent']//div[contains(@class,'WB_text')]//text()")
        content_ele[0] = content_ele[0].strip()
        content = "\n".join(content_ele).replace("\u200b", "").replace("//\n@", "//@").replace("\n:", ":").replace(
            "\xa0", "").replace("\xa1", "")
        # 有链接时会多出换行，可以在xpath处理但是太麻烦，所以直接replace
        content = content.replace("\nO\n网页链接", " O 网页链接")

        # 链接
        parse_links = parse.xpath(".//div[@node-type='feed_list_content']//a[@href and @rel]/@href")
        real_links = []
        for parse_link in parse_links:
            # try是有时候会有外网链接，请求失败
            try:
                link_response = session.get(parse_link)
                response_url = link_response.url

                if response_url != parse_link:
                    # 直接将请求到的url放入列表
                    real_links.append(response_url)
                else:
                    # 需要从页面中解析出真正的url
                    real_link = etree.HTML(link_response.text).xpath(".//div[contains(@class,'desc')]/text()")[
                        0].strip()
                    real_links.append(real_link)

            except:
                real_links.append(parse_link)

        # 发表时间
        public_time = str(parse.xpath(".//div[contains(@class,'WB_from')]/a/@title")[0])
        # 发表时间戳
        public_timestamp = int(parse.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])

        # 图片链接
        img_list = []

        item_eles = parse.xpath(".//div[contains(@class,'WB_media_wrap clearfix')]//div[contains(@class,'media_box')]")
        # 存在item_ele
        if item_eles:
            item_ele = item_eles[0]
            img_info_list = item_ele.xpath(".//li[contains(@class,'WB_pic')]/@suda-uatrack")
            # 存在图片ele
            if img_info_list:
                img_list = [self.__get_img_list(img_info) for img_info in img_info_list]
            else:
                img_list = []

        # 视频
        video_url = ""
        video_url_info = parse.xpath(".//li[contains(@class,'WB_video')]/@suda-uatrack")
        # 只保留原创视频链接
        if video_url_info:
            video_url_base = "https://weibo.com/tv/show/{}:{}"
            video_search = re.search(r":(\d+)%3A(\w+):", video_url_info[0])
            video_url = video_url_base.format(video_search.group(1), video_search.group(2))

        # 微博来源
        weibo_from_ele = parse.xpath(".//div[contains(@class,'WB_from')]//a[@action-type]/text()")
        if weibo_from_ele:
            weibo_from = weibo_from_ele[0]
        else:
            weibo_from = "未显示来源"

        # 文章 链接和内容
        article_url = ""
        article_content = ""
        article_url_ele = parse.xpath(".//div[contains(@class,'WB_feed_spec')]/@suda-uatrack")

        # 存在外链div
        if article_url_ele:
            article_url_base = "https://weibo.com/ttarticle/p/show?id={}"
            article_id_search = re.search(r"article:（\d+）:", article_url_ele[0])
            # 外链div为文章
            if article_id_search:
                article_url = article_url_base.format(article_id_search.group(1))
                article_parse = etree.HTML(session.get(article_url).text)
                article_content = "\n".join(article_parse.xpath(".//div[@node-type='contentBody']/p/text()"))
        # 赞  评论 转发
        forward_comment_like_ele = parse.xpath(".//span[@class='line S_line1']/a/span//em[last()]/text()")
        # 肯定有转发，不用判断
        forward_num = int(forward_comment_like_ele[0])
        comment_ele = forward_comment_like_ele[1]
        if "评论" not in comment_ele:
            comment_num = int(comment_ele)
        else:
            comment_num = 0
        like_ele = forward_comment_like_ele[2]
        if "赞" not in like_ele:
            like_num = int(like_ele)
        else:
            like_num = 0
        # 调这个方法的绝对是原创公开微博，且获取不到评论
        is_original = 1
        share_scope = "公开"
        comment_list = []
        r_href = ""
        r_weibo = {}

        a_weibo = weibo(bid, weibo_url, user_id, user_name, content, public_time, public_timestamp,
                        share_scope, like_num, forward_num, comment_num, comment_list, is_original,
                        r_href, real_links, img_list, video_url, weibo_from, article_url,
                        article_content, remark, r_weibo)
        return a_weibo

    def parse_weibo_from_div(self, weibo_div, session, config):
        """
        解析微博的div，创建weibo对象
        :param weibo_div: //div[@tbinfo]
        :param session:
        :param config:
        :return:
        """
        # 备注
        remark = ""
        parse = weibo_div

        count = 0
        # 微博链接
        while True:
            if count > 10:
                print("调用parse_weibo_from_div的参数有误，返回空weibo对象")
                time.sleep(3)
                return self.get_null_weibo()
            count += 1
            try:
                weibo_url = "https://weibo.com" + parse.xpath("//div[contains(@class,'WB_from')]/a/@href")[0]
                break
            except:
                pass
        if config["print_level"]:
            print("开始解析链接 {}".format(weibo_url))
        # 用户id，微博为转发时格式为 ‘ouid=6123910030&rouid=5992829552’
        user_id_ele = parse.xpath(".//@tbinfo")[0].split("&")[0]
        user_id = re.search(r"ouid=(\d+)", user_id_ele).group(1)

        # bid
        bid_ele = parse.xpath(".//a[@node-type='feed_list_item_date']/@href")
        bid = re.search("/\d+/(\w+)\?", bid_ele[0]).group(1)

        # 用户名，同时判断是否为快转
        quick_transmit = 0
        user_name = parse.xpath(".//a[@class='W_f14 W_fb S_txt1']/text()")

        if not user_name:
            user_name = parse.xpath(".//a[contains(@class,'W_f14 W_fb S_txt1')]/text()")
            quick_transmit = 1
        user_name = user_name[0]

        # 是否为原创微博，转发微博源微博的相对地址
        trainsmig_ele = parse.xpath(".//div[@class='WB_feed_expand']")
        if trainsmig_ele:
            # 是转发微博
            is_original = 0
            if len(bid_ele) > 1:
                r_href = bid_ele[1]
            else:
                r_href = "源微博已不可见"

                remark += "转发微博的原微博不可见\t"
        else:
            if quick_transmit:
                # 是快转微博
                is_original = -1
            else:
                # 是原创微博
                is_original = 1
            r_href = ""

        print(weibo_url)
        # 正文
        # 文章长时会有收起的部分，需要另外发送请求
        is_content_long = parse.xpath(".//a[contains(@class,'WB_text_opt')]")
        # 如果有折叠的部分
        if is_content_long:
            content_parse = self.get_weibo_div(session, weibo_url)
            content_ele = content_parse.xpath(".//div[@node-type='feed_list_content']//text()")

        else:
            content_ele = parse.xpath(".//div[@node-type='feed_list_content']//text()")
        # 取出0的首尾空格
        content_ele[0] = content_ele[0].strip()
        content = "\n".join(content_ele).replace("\u200b", "").replace("//\n@", "//@").replace("\n:", ":").replace(
            "\xa0", "").replace("\xa1", "")
        # 有链接时会多出换行，可以在xpath处理但是太麻烦，所以直接replace
        content = content.replace("\nO\n网页链接", " O 网页链接")

        # 外链，微博有的链接进行一次请求才能获取到真正的链接，有的需要从确认界面中获取
        parse_links = parse.xpath(".//div[@node-type='feed_list_content']//a[@href and @rel]/@href")
        real_links = []
        for parse_link in parse_links:
            # try是有时候会有外网链接，请求失败
            try:
                link_response = session.get(parse_link)
                response_url = link_response.url

                if response_url != parse_link:
                    # 直接将请求到的url放入列表
                    real_links.append(response_url)
                else:
                    # 需要从页面中解析出真正的url
                    real_link = etree.HTML(link_response.text).xpath(".//div[contains(@class,'desc')]/text()")[
                        0].strip()
                    real_links.append(real_link)

            except:
                real_links.append(parse_link)

            # 是否直接跳转

        # 可见范围
        share_scope_ele = parse.xpath(".//div[contains(@class,'WB_cardtitle_b')]")
        if share_scope_ele:
            share_scope = share_scope_ele[0].xpath(".//span[@class='WB_type']/text()")[0]
        else:
            share_scope = "公开"

        # 转发数
        forward_num_ele = parse.xpath(".//span[@node-type='forward_btn_text']//text()")
        forward_num = 0
        if forward_num_ele:
            forward_num_str = forward_num_ele[1]
            if forward_num_str != "转发":
                forward_num = int(forward_num_str)
        # 评论数
        comment_num_str = parse.xpath(".//span[@node-type='comment_btn_text']//text()")[1]
        if comment_num_str != "评论":
            try:
                comment_num = int(comment_num_str)
            except:
                if "万" in comment_num_str:
                    comment_num = int(comment_num_str.split("万")[0]) * 10000
                else:
                    comment_num = -1
                remark += "\t 评论数异常，获取到的字符串为：{}".format(comment_num_str)
        else:
            comment_num = 0
        # 点赞数
        # 是转发微博且原微博存在时 取下标1，否则0
        my_like_index = 1 if (not is_original and r_href != "源微博已不可见") else 0
        like_num_ele = parse.xpath(".//span[@node-type='like_status']")[my_like_index]
        like_num_str = like_num_ele.xpath(".//text()")[-1]
        if like_num_str != "赞":
            like_num = int(like_num_str)
        else:
            like_num = 0

        # 发表时间
        public_time = str(parse.xpath(".//div[contains(@class,'WB_from')]/a/@title")[0])
        # 发表时间戳
        public_timestamp = int(parse.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])

        item_eles = parse.xpath(".//div[contains(@class,'WB_media_wrap clearfix')]//div[contains(@class,'media_box')]")
        # 图片链接
        img_list = []

        # 存在item_ele
        if item_eles and is_original:
            item_ele = item_eles[0]
            img_info_list = item_ele.xpath(".//li[contains(@class,'WB_pic')]/@suda-uatrack")
            # 存在图片ele
            if img_info_list:
                img_list = [self.__get_img_list(img_info) for img_info in img_info_list]
            else:
                img_list = []

        # 视频
        video_url = ""
        video_url_info = parse.xpath(".//li[contains(@class,'WB_video')]/@suda-uatrack")
        # 只保留原创视频链接
        if video_url_info and is_original:
            video_url_base = "https://weibo.com/tv/show/{}:{}"
            video_search = re.search(r":(\d+)%3A(\w+):", video_url_info[0])
            try:
                video_url = video_url_base.format(video_search.group(1), video_search.group(2))
            except:
                remark += "\t 该条微博带有直播视频"
        # 微博来源
        weibo_from_ele = parse.xpath(".//div[contains(@class,'WB_from')]//a[@action-type]/text()")
        if weibo_from_ele:
            weibo_from = weibo_from_ele[0]
        else:
            weibo_from = "未显示来源"

        # 文章 链接和内容
        article_url = ""
        article_content = ""
        article_url_ele = parse.xpath(".//div[contains(@class,'WB_feed_spec')]/@suda-uatrack")

        # 存在外链div
        if article_url_ele:
            article_url_base = "https://weibo.com/ttarticle/p/show?id={}"
            article_id_search = re.search(r"article:（\d+）:", article_url_ele[0])
            # 外链div为文章
            if article_id_search:
                article_url = article_url_base.format(article_id_search.group(1))
                article_parse = etree.HTML(session.get(article_url).text)
                article_content = "\n".join(article_parse.xpath(".//div[@node-type='contentBody']/p/text()"))
        comment_list = []
        # 如果有评论
        if comment_num:
            print("有评论，准备解析评论")
            # 只有设置了保存全部评论，且当前用户是需要爬取全部评论的，get_all_comment才为True
            get_all_comment = config["get_all_comment"] and (
                    user_id == config["user_id"] or user_id in config["additional_user_ids"])
            comment_list = self.__get_comment_list(parse, session, get_all_comment)
            if get_all_comment and len(comment_list) < comment_num:
                remark += "部分评论无法获取(一般是被吞了)\t"
        elif len(comment_list) > comment_num:
            remark += "由于评论数获取时间早于评论获取时间，评论实际获取数x量大于解析评论数\t"
        r_weibo = {}
        if r_href and "源微博已不可见" not in r_href:
            r_url = "https://weibo.com/" + r_href
            print("微博为转发微博，开始解析源微博 {}".format(r_url))
            r_div = self.get_weibo_div(session, r_url)
            # 源微博绝对是原创微博，不会有r_weibo，所以调with_simple_r_weibo没问题
            # if r_div:
            if len(r_div):
                r_weibo = self.parse_weibo_from_div(r_div, session, config).to_dict_with_simple_r_weibo()
            else:
                print("无法获取到源微博，对源微博进行简单解析")
                forward_div = parse.xpath(".//div[contains(@class,'WB_feed_expand')]")[0]
                r_weibo = self.parse_weibo_from_forward_div(session, forward_div).to_dict_with_simple_r_weibo()

        # 话题，@的用户，地址    不想写，以后可能会补上
        topic_list = []
        call_users = []
        address = ""
        a_weibo = weibo(bid, weibo_url, user_id, user_name, content, public_time, public_timestamp,
                        share_scope, like_num, forward_num, comment_num, comment_list, is_original,
                        r_href, real_links, img_list, video_url, weibo_from, article_url,
                        article_content, remark, r_weibo)
        return a_weibo

    def __get_img_list(self, img_info):
        # 解析图片列表
        img_url_base = "https://photo.weibo.com/{}/wbphotos/large/mid/{}/pid/{}"
        img_match = re.search(r":(\d+):(\w+):(\d+)", img_info)
        img_url = img_url_base.format(img_match.group(3), img_match.group(1), img_match.group(2))
        return img_url

    # 通过id获取所有评论
    def __get_comment_list(self, parse, session, get_all_comment):

        # 所有评论列表
        all_comment_list = []
        # 评论统计
        root_comment_count = 0
        all_comment_count = 0
        # 取得id
        id = parse.xpath("//div[contains(@class,'WB_from')]/a/@name")[0]
        # 前15条评论
        first_comment_url_base = "https://weibo.com/aj/v6/comment/big?ajwvr=6&id={}&from=singleWeiBo&__rnd={}"
        root_error_count = 0
        # 避免失败，重复请求
        while True:
            first_comment_url = first_comment_url_base.format(id, int(time.time() * 1000))
            root_comment_response_html = session.get(first_comment_url).json()["data"]["html"]
            comment_parse = etree.HTML(root_comment_response_html)
            write_file(root_comment_response_html, "comment-root.html")
            # first_comment_div_list = comment_parse.xpath("//div[@comment_id and @node-type='root_comment']")
            first_comment_div_list = comment_parse.xpath("//div[contains(@node-type,'comment_list')]/div[@comment_id]")
            root_comment_count += len(first_comment_div_list)
            # 请求到评论内容 跳出循环
            if first_comment_div_list:
                print("获取到 comment-root {} 条".format(len(first_comment_div_list)))
                break
            # 评论被吞了，或者断网
            if root_error_count > 10:
                print("无法获取到评论")
                break

            root_error_count += 1
            if root_error_count % 3 == 0:
                print("comment-root已请求失败{}次".format(root_error_count))
            time.sleep(1)

        # 将每条评论和子评论 解析出来添加到总列表中
        for comment_div in first_comment_div_list:
            a_group_comment_info = self.__parse_comment(comment_div, get_all_comment)
            all_comment_list += a_group_comment_info
            all_comment_count += len(a_group_comment_info)

        # 如果不要求获取所有评论，只获取前15条即可返回
        if not get_all_comment:
            if all_comment_list:
                print("成功获取到前15条root评论")

            return all_comment_list

        # 获取所有评论
        """
        跟前15条评论的代码重复度很高
        """
        next_url = comment_parse.xpath("//div[@node-type='comment_loading']/@action-data")
        flag = 1
        if not next_url:
            # 这种是旧的翻页url，2016之前都是这种
            next_url = comment_parse.xpath("//a[contains(@class,'page next')]/span/@action-data")
            flag = 0

        # 一直获取，直到没有下一评论
        while next_url:
            sub_error_count = 0
            sub_comment_div_list = []
            # 重复请求，直到请求成功
            while True:
                sub_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}".format(
                    next_url[0], int(time.time() * 1000))
                sub_comment_response_html = session.get(sub_comment_url).json()["data"]["html"]
                write_file(sub_comment_response_html, "comment-root-sub.html")
                sub_comment_parse = etree.HTML(sub_comment_response_html)
                # sub_comment_div_list = sub_comment_parse.xpath("//div[@comment_id and @node-type='root_comment']")
                sub_comment_div_list = sub_comment_parse.xpath(
                    "//div[contains(@node-type,'comment_list')]/div[@comment_id]")
                # 请求到则跳出循环
                if sub_comment_div_list:
                    print("获取到 comment-root-sub  {} 条".format(len(sub_comment_div_list)))
                    root_comment_count += len(sub_comment_div_list)
                    break
                sub_error_count += 1
                if sub_error_count % 3 == 0:
                    print("comment-root-sub已请求失败{}次".format(sub_error_count))
                    time.sleep(3)
                if sub_error_count > 9:
                    print("无法获取到该部分的 comment-root-sub，跳过")
                    break
                time.sleep(3)
            # 将新获取到的评论和子评论 解析出来添加到总列表中
            for sub_comment_div in sub_comment_div_list:
                new_sub_comment_list = self.__parse_comment(sub_comment_div, get_all_comment)
                all_comment_list += new_sub_comment_list
                all_comment_count += len(new_sub_comment_list)

            # 更新next_url，获取后面的评论
            if flag:
                next_url = sub_comment_parse.xpath("//div[@node-type='comment_loading']/@action-data")
            else:
                next_url = sub_comment_parse.xapth("//a[contains(@class,'page next')]/span/@action-data")
            if not next_url:
                next_url = sub_comment_parse.xpath("//a[@action-type='click_more_comment']/@action-data")
        print("共获取到评论 {} 条，其中root评论 {} 条".format(all_comment_count, root_comment_count))
        return all_comment_list

    # 解析每条评论的div
    def __parse_comment(self, comments_div, get_all_comment):
        # 最终返回的列表
        a_group_comment_info = []
        # 所有评论的div
        all_group_div_list = []
        # root评论的div
        root_comment_div = comments_div.xpath(".//div[@class='list_con'and @node-type]")[0]
        all_group_div_list.append(root_comment_div)
        # 一部分直接显示的子评论
        child_comment_out_divs = comments_div.xpath(".//div[@node-type='child_comment']//div[@class='list_con']")
        # 是否获取所有评论
        if get_all_comment:
            # 有无"加载更多"
            sub_child_comment_url_part = comments_div.xpath(
                ".//a[@action-type='click_more_child_comment_big']/@action-data")
            # 如直接显示的子评论在加载更多时会再加载一次，所没有加载更多时才保存out子评论
            if not sub_child_comment_url_part and child_comment_out_divs:
                all_group_div_list += child_comment_out_divs
                if child_comment_out_divs:
                    print("获取到 comment-child-out {} 条".format(len(child_comment_out_divs)))

            # 当有下一页
            while sub_child_comment_url_part:
                sub_child_error_count = 0
                while True:
                    sub_child_comment_url = "https://weibo.com/aj/v6/comment/big?ajwvr=6&{}&from=singleWeiBo&__rnd={}".format(
                        sub_child_comment_url_part[0], int(time.time() * 1000))
                    sub_child_comment_html = session.get(sub_child_comment_url).json()["data"]["html"]
                    sub_child_comment_parse = etree.HTML(sub_child_comment_html)
                    new_sub_child_comment_divs = sub_child_comment_parse.xpath(
                        "//div[@comment_id]//div[@class='list_con']")
                    # 成功获取到新的子评论
                    if new_sub_child_comment_divs:
                        print("获取到 comment-child-in {} 条".format(len(new_sub_child_comment_divs)))
                        time.sleep(0.5)
                        break
                    sub_child_error_count += 1
                    if sub_child_error_count % 3 == 0:
                        print("comment-child-sub已请求失败{}次".format(sub_child_error_count))
                        time.sleep(2.5)
                all_group_div_list += new_sub_child_comment_divs
                # 更新下一页子评论的请求url
                sub_child_comment_url_part = sub_child_comment_parse.xpath(
                    "//a[@action-type='click_more_child_comment_big']/@action-data")
        else:
            # 不保存全部评论的也会保存out子评论，但不一定有
            all_group_div_list += child_comment_out_divs
            if child_comment_out_divs:
                print("获取到 comment-child-out {} 条".format(len(child_comment_out_divs)))

        # 解析评论div，root div和child div可以用相同xpath路径
        root_comment_content_and_user = ""
        for comment_div in all_group_div_list:
            # 一条root/child评论信息
            comment_info = {}
            # 评论内容
            comment_content_and_user = "".join(comment_div.xpath("./div[contains(@class,'WB_text')]//text()")) \
                .encode("gbk", errors="replace").decode("gbk", errors="replace").replace("\n            ", "")
            comment_content = comment_content_and_user.split("：", 1)[1].strip()
            comment_info["content"] = comment_content
            # 评论人
            user_name = comment_div.xpath(".//div[contains(@class,'WB_text')]/a/text()")[0]
            comment_info["user_name"] = user_name
            # 评论人主页链接
            user_url = "https:" + comment_div.xpath(".//div[contains(@class,'WB_text')]/a/@href")[0]
            comment_info["user_url"] = user_url
            # 评论时间
            comment_date = comment_div.xpath(".//div[contains(@class,'WB_from')]/text()")[0]
            comment_date = self.__deal_comment_date(comment_date)
            comment_info["comment_date"] = comment_date
            # 评论是根评论还是子评论，该评论的父评论
            if all_group_div_list.index(comment_div) == 0:
                # 根评论
                comment_type = "root"
                parent_comment = "/"
                root_comment_content_and_user = comment_content_and_user
            else:
                # 子评论
                comment_type = "child"
                parent_comment = root_comment_content_and_user

            comment_info["comment_type"] = comment_type
            comment_info["parent_comment"] = parent_comment
            # 评论点赞数
            comment_like_eles = comment_div.xpath(".//span[@node-type='like_status']//text()")
            if comment_type == "root":
                comment_like_str = comment_like_eles[1]
            else:
                comment_like_str = comment_like_eles[-1]
            if comment_like_str != "赞":
                like_num = int(comment_like_str)
            else:
                like_num = 0
            comment_info["like_num"] = like_num
            # 评论带图
            comment_img_url = ""
            if comment_type == 'root':
                # root用跟child一样的方法也能获取到图片,但是写的这种获取的图片更高清
                img_ele = comment_div.xpath(".//li/img/@src")
                if img_ele:
                    img_url = img_ele[0].replace("thumb180", "large")
                    comment_img_url = img_url
            else:
                img_info = comment_div.xpath(".//a[@alt]/@action-data")
                if img_info:
                    img_url_base = "https://wx3.sinaimg.cn/large/{}.jpg"
                    img_pid = re.search("pid=(\w.*?)&", img_info[0])
                    comment_img_url = img_url_base.format(img_pid.group(1))
                    print(comment_img_url)
            comment_info["comment_img_url"] = comment_img_url

            # 链接
            comment_link_ele = comment_div.xpath("./div[@class='WB_text']/a/@alt")
            comment_link = ""
            if comment_link_ele:
                comment_link = comment_link_ele[0]
            comment_info["comment_link"] = comment_link

            a_group_comment_info.append(comment_info)

        return a_group_comment_info

    def __deal_comment_date(self, comment_time: str):
        """
        评论时间太近会出现 "今天 20:20","10分钟前","10秒前"的格式，需要转为标准时间
        :param comment_time:
        :return:
        """
        if "今天" in comment_time:
            patten = "%Y-%m-%d"
            today_time = time.localtime(time.time())
            today_date_str = time.strftime(patten, today_time)
            comment_time_result = comment_time.replace("今天", today_date_str)
        elif "前" in comment_time:
            patten = "%Y-%m-%d %H:%M"
            if "秒" in comment_time:
                sec = int(comment_time.replace("秒前", ""))
                comment_timestamp = time.time() - sec
                comment_time_result = time.strftime(patten, time.localtime(comment_timestamp))
            elif "分钟" in comment_time:
                sec = int(comment_time.replace("分钟前", "")) * 60
                comment_timestamp = time.time() - sec
                comment_time_result = time.strftime(patten, time.localtime(comment_timestamp))

            else:
                comment_time_result = comment_time
                print("时间解析有误")
        else:
            comment_time_result = comment_time
        return comment_time_result

    def init_sql(self):
        pass

        # create_database_sql = "create database if not exists weibo"
        # create_table_sql = """create table if not exists {}
        # (
        # )
        # """.format(self.talbe_name)
        # cursor = self.sql_conn.cursor()
        # cursor.execute(create_database_sql)
        # cursor.execute(create_table_sql)

    def save_to_sql(self):
        pass


# 更新json文件
def update_json_file(json_file, file_name, coding="utf-8"):
    file_str = json.dumps(json_file, indent=4, ensure_ascii=False)
    open(file_name, "w", encoding=coding).write(file_str)


# 读取json文件
def read_json(file_name, coding="utf-8"):
    file1 = open(file_name, "r", encoding=coding).read()

    try:
        content = json.loads(file1)
    except:
        print("{} 文件格式错误 ，程序退出".format(file_name))
        sys.exit()
    return content


# 快速写文件，主要用于测试
def write_file(file, file_name="./test.html", coding="utf-8"):
    file_path = "test"
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    open(file_path + "/" + file_name, "w", encoding=coding).write(file)


def CookiestoDic(str):
    result = {}

    cookies = str.split(";")
    # print(cooks)
    cookies_pattern = re.compile("(.*?)=(.*)")
    for cook in cookies:
        # print(cook)
        cook = cook.replace(" ", "")
        header_name = cookies_pattern.search(cook).group(1)
        header_value = (cookies_pattern.search(cook).group(2))
        result[header_name] = header_value

    return result


def is_b_later_than_a(a, b):
    """
    时间比较
    :param a: 时间戳或 "%Y-%m-%d %H:%M"格式的字符串
    :param b: 时间戳或 "%Y-%m-%d %H:%M"格式的字符串
    :return: boolean
    """
    patten = "%Y-%m-%d %H:%M"
    if type(a) == str:
        time_a = time.strptime(a, patten)
        timestamp_a = time.mktime(time_a) * 1000
        str_a = a
    elif type(a) == int:
        timestamp_a = a

    else:
        print("参数a应为int或str类型，返回0")
        timestamp_a = 0

    if type(b) == str:
        time_b = time.strptime(b, patten)
        timestamp_b = time.mktime(time_b) * 1000
    elif type(b) == int:
        timestamp_b = b
    else:
        timestamp_b = 0
        print("参数a应为int或str类型,返回0")
    result = timestamp_b - timestamp_a
    return result > 0


def get_page_div_list(page, user_id, session):
    """
    获取一页微博的div
    :param page: 要获取的页数
    :param session: requests.session()
    :return: list 返回获取到的微博divs
    """
    first_part_url_base = "https://weibo.com/{}?page={}&is_all=1"
    sub_part_url_base = "https://weibo.com/p/aj/v6/mblog/mbloglist?ajwvr=6&domain=100505&visible=0&is_all=1" \
                        "&profile_ftype=1&page={}&pagebar={}&pl_name=Pl_Official_MyProfileFeed__20" \
                        "&id=100505{}&script_uri=/{}/profile&feed_type=0&pre_page={}&domain_op=100505&__rnd={} "
    a_page_div_list = []

    # 每页加载的第一部分
    first_part_url = first_part_url_base.format(user_id, page)
    first_part_response = session.get(first_part_url)
    parse = etree.HTML(first_part_response.content.decode("utf-8"))
    # 将需要的html从里面提取出来
    scripts = parse.xpath("//script")
    re_s = re.search(r"\(({.*})\)", scripts[-1].text)
    html_text = json.loads(re_s.group(1))["html"]

    # 测试
    write_file(html_text, "text0.html")
    # 解析出微博div
    parse = etree.HTML(html_text)
    first_divs = parse.xpath("//div[@tbinfo]")

    # 将解析出的div加入总列表
    a_page_div_list += first_divs
    print(len(first_divs), end="\t")

    # 后两部分
    for part in range(0, 2):
        sub_part_url = sub_part_url_base.format(page, part, user_id, user_id, page, int(time.time() * 1000))
        sub_reponse = session.get(sub_part_url)
        # 从json中提取出html
        sub_html = sub_reponse.json()["data"]
        # 测试
        write_file(sub_html, "test{}.html".format(part + 1))
        sub_parse = etree.HTML(sub_html)
        sub_divs = sub_parse.xpath("//div[@tbinfo]")
        a_page_div_list += sub_divs
        print(len(sub_divs), end="\t")
    print()
    real_div_list = []
    # 过滤掉点赞
    filter_num = 0

    for div in a_page_div_list:
        share_scope_ele = div.xpath(".//div[contains(@class,'WB_cardtitle_b')]")
        if share_scope_ele:
            he_like = share_scope_ele[0].xpath(".//span[@class='subtitle']")
            if he_like:
                filter_num += 1
                continue

        real_div_list.append(div)
    if filter_num:
        print("过滤掉点赞微博 {} 条,剩余 {} 条".format(filter_num, len(real_div_list)))
    return real_div_list


def download_weibo_file(config, session, schedule_filename, download_filename):
    """
    下载微博div，将文件以list（json）格式保存到download_filename
    :param config: 配置文件
    :param session: request.seesion
    :param schedule_filename: 进度文件名
    :param download_filename: 下载文件名
    :return: 五
    """
    # 配置文件
    all_page = config["all_page"]
    user_id = config["user_id"]
    # 读取上次的进度
    schedule = read_json(schedule_filename)
    downloaded_page = schedule["downloaded"]
    all_div_str_list = read_json(download_filename)
    if all_div_str_list:
        print("读取到上次下载的微博 {} 条".format(len(all_div_str_list)))
    if downloaded_page:
        print("读取到上次运行的进度，已下载完成 {} 页，微博 {} 条".format(downloaded_page, len(all_div_str_list)))
    for page in range(downloaded_page + 1, all_page + 1):
        # 异常次数（请求失败次数）
        exception_count = 0
        # 请求成功但是获取微博条数不够的次数
        flag = 0
        print("对第 {} 页发起请求".format(page))
        # 该页的微博div标签
        page_divs = []
        # 获取到的div数量
        page_div_num = 0
        # 多次请求中获取到的div最大数量
        max_div_num = 0
        # 一般一页有45条，未请求到时重新请求（有置顶的第1页有46条，但是懒得整）
        while page_div_num < 45:
            # 异常次数过多休眠
            if exception_count != 0 and exception_count % 3 == 0:
                time.sleep(8)
            # 超过3次正常请求数量不够,说明这页就这么多，微博的错，或者是最后一页，直接跳出循环
            if flag > 6 and max_div_num == page_div_num:
                print("{}页确实就这么多".format(page))
                break

            try:
                # 对页面发起请求
                page_divs = get_page_div_list(page, user_id, session)
                page_div_num = len(page_divs)
            except:
                print("\n请求 {} 页过程报错，重新发起请求".format(page))
                exception_count += 1
                time.sleep(3)
                continue

            # 反复获取中获取到的最多条数
            if page_div_num > max_div_num:
                max_div_num = page_div_num
            # 返回微博条数不够
            if page_div_num < 45:
                # 重新请求
                print("{} 页响应异常，重新发起请求".format(page))
                flag += 1
                time.sleep(4)
                continue

        # 过滤，包括等于stop_time的，不包括等于start_time的
        # 获取顺序是从晚到早
        # update_mode时start_time为update_start_time
        start_time = config["update_start_time"] if config["update_mode"] else config["start_time"]
        stop_time = config["stop_time"]
        if stop_time:
            earliest_div = page_divs[-1]
            # 最早的微博晚于stop_time，跳过该页
            earliest_public_timestamp = earliest_div.xapth("//div[contains(@class,'WB_from')]/a/@date")[0]
            if not is_b_later_than_a(earliest_public_timestamp, stop_time):
                print("第{}页微博不在指定时间范围内 - stop_time".format(page))
                continue
        if start_time:
            # 如果有置顶的话，选择第二条作为最晚div
            first_content = "".join(page_divs[0].xpath(".//div[@node-type='feed_list_content']//text()"))
            if "置顶" in first_content:
                newest_div = page_divs[1]
            else:
                newest_div = page_divs[0]
            newest_public_timestamp = int(newest_div.xpath(".//div[contains(@class,'WB_from')]/a/@date")[0])
            # 该页最晚(新)的微博 早于/等于start_time,直接跳出循环
            if is_b_later_than_a(newest_public_timestamp, start_time):
                print("第{}页微博不在指定时间范围内 - start_time".format(page))
                print("已获取到指定时间内的所有微博")
                break

            # 将数据添加到列表
        for div in page_divs:
            all_div_str_list.append(etree.tostring(div, encoding="utf-8").decode("utf-8"))
        print("第 {} 页请求到微博 {} 条".format(page, page_div_num))

        # 刷新进度文件与下载文件
        if page % 4 == 0 or page == all_page:
            schedule["downloaded"] = page
            update_json_file(all_div_str_list, download_filename)
            update_json_file(schedule, schedule_filename)
            print("文件刷新")
        # 每下载一页停4秒
        time.sleep(4)

    # 再次刷新保存的div文件
    update_json_file(all_div_str_list, download_filename)
    # 更新进度文件
    schedule["parsed"] = 0
    schedule["downloaded"] = "done"
    update_json_file(schedule, schedule_filename)
    print("下载完成，共获取到微博 {} 条".format(len(all_div_str_list)))


def parse_weibo(session, weibo_divs, config, schedule_filename, result_filename):
    schedule = read_json(schedule_filename)
    parse_schedule = schedule["parsed"]
    weibo_list = read_json(result_filename)
    r_weibo_list = read_json(r_result_filename)
    weibo_tool1 = WeiboTool()
    to_parse = len(weibo_divs) - 1 - parse_schedule
    if weibo_list:
        print("读取到上次解析的微博 {} 条".format(len(weibo_list)))
    # 从早到晚保存的
    for div_str in weibo_divs[to_parse::-1]:

        print("--------------------------")
        div = etree.HTML(div_str)
        weibo1 = weibo_tool1.parse_weibo_from_div(div, session, config)
        public_time = weibo1.public_time

        # 过滤，包括等于stop_time的，不报错等于start_time的
        # 顺序是从早到晚
        # start_time = config["start_time"]
        start_time = config["update_start_time"] if config["update_mode"] else config["start_time"]
        stop_time = config["stop_time"]
        if stop_time:
            if not is_b_later_than_a(public_time, stop_time):
                # 微博晚于stop_time，且非置顶,直接跳出循环
                if "置顶" not in weibo1.content:
                    print("已解析指定时间范围内所有微博，解析结束")
                    # 更新文件后直接退出
                    parse_schedule = len(weibo_divs)
                    schedule["parsed"] = parse_schedule
                    update_json_file(schedule, schedule_filename)
                    update_json_file(weibo_list, result_filename)
                    break
                else:
                    # 微博晚于stop_time，是置顶,跳过
                    parse_schedule += 1
                    print("该微博不在指定时间范围内")
                    print("解析进度 {}/{}".format(parse_schedule, len(weibo_divs)))

                    # 文件刷新
                    if parse_schedule % 5 == 0 or parse_schedule == len(weibo_divs) - 1:
                        schedule["parsed"] = parse_schedule
                        update_json_file(schedule, schedule_filename)
                        print("文件刷新")
                    continue
        if start_time:
            # 微博早于/等于start_time,跳过
            if is_b_later_than_a(public_time, start_time):
                parse_schedule += 1
                print("该微博不在指定时间范围内，被过滤掉")
                print("解析进度 {}/{}".format(parse_schedule, len(weibo_divs)))
                # 文件刷新
                if parse_schedule % 5 == 0 or parse_schedule == len(weibo_divs) - 1:
                    schedule["parsed"] = parse_schedule
                    update_json_file(schedule, schedule_filename)
                    print("文件刷新")
                continue

        # 将微博信息添加到列表
        weibo_info_dict = weibo1.to_dict_with_simple_r_weibo()
        weibo_list.append(weibo_info_dict)
        # 如果有转发微博，且不是更新模式
        if weibo1.r_weibo and not config["update_mode"]:
            r_weibo_list.append(weibo1.r_weibo)
        parse_schedule += 1
        try:
            print("当前微博解析完毕： {}".format(weibo_info_dict))
        except:
            print("这行出不来")
        print("解析进度 {}/{}".format(parse_schedule, len(weibo_divs)))

        # 文件刷新k
        if parse_schedule % 5 == 0 or parse_schedule == len(weibo_divs) - 1:
            schedule["parsed"] = parse_schedule
            update_json_file(schedule, schedule_filename)
            update_json_file(weibo_list, result_filename)
            update_json_file(r_weibo_list, r_result_filename)
            print("文件刷新")
    schedule["parsed"] = "done"
    update_json_file(schedule, schedule_filename)
    update_json_file(weibo_list, result_filename)
    print("文件刷新")

    print("解析完成,共计主页微博 {} 条，源微博 {} 条".format(len(weibo_list), len(r_weibo_list)))


def get_user_ident(config, session):
    """
    获取用户标识 用户名[用户id]
    :param config:
    :param session:
    :return:
    """
    user_id = config["user_id"]
    base_url = "https://weibo.com/{}?page=1&is_all=1".format(user_id)
    user_name = ""
    while True:
        try:
            first_part_response = session.get(base_url)
            parse = etree.HTML(first_part_response.content.decode("utf-8"))
            scripts = parse.xpath("//script")
            re_s = re.search(r"\(({.*})\)", scripts[-1].text)
            html_text = json.loads(re_s.group(1))["html"]
            parse = etree.HTML(html_text)
            user_name = parse.xpath("//div[contains(@class,'WB_info')]/a/text()")[0]
            if user_name:
                break
        except:
            pass

    user_ident = "{}[{}]".format(user_name, user_id)
    return user_ident


def check_run_file(user_ident, schedule_filename, download_filename, result_filename, r_result_filename):
    """
    文件检查
    """
    print("检查运行文件")
    file_path = "./" + user_ident
    if not os.path.exists(file_path):
        os.mkdir(file_path)
        print("创建文件夹 {}".format(file_path))

    if not os.path.exists(schedule_filename):
        schedule = {
            "downloaded": 0,
            "parsed": 0,
            "saved": 0
        }
        update_json_file(schedule, schedule_filename)
        print("初始化文件 {}".format(schedule_filename))
    if not os.path.exists(download_filename):
        update_json_file([], download_filename)
        print("初始化文件 {}".format(download_filename))
    if not os.path.exists(result_filename):
        update_json_file([], result_filename)
        print("初始化文件 {}".format(result_filename))
    if not os.path.exists(r_result_filename):
        update_json_file([], r_result_filename)
        print("初始化文件 {}".format(r_result_filename))
    print("检查完成")


def check_config_file(config_filename):
    """
    配置文件检查，报错返回1，否则返回0
    :param config_filename:
    :return:
    """
    # 文件是否存在
    print("检查配置文件")
    if not os.path.exists(config_filename):
        print("配置文件不存在，程序退出")
        return 1
    print("检查配置项")
    # 配置项是否存在
    config = read_json(config_filename)
    keys = ['user_id', 'all_page', 'cookies', 'get_all_comment', 'additional_user_ids', 'start_time', 'stop_time',
            'auto_get_increment', 'update_mode', "update_start_time", 'print_level']
    for key in keys:
        try:
            value = config[key]
        except:
            print("配置项 {} 不存在，程序退出".format(key))
            return 1
    # 配置项类型检查
    int_keys = ["all_page", "get_all_comment", "auto_get_increment", "update_mode", "print_level"]
    for key in int_keys:
        if type(config[key]) != int:
            print("配置项 {} 应为int类型，程序退出".format(key))
            return 1
    str_keys = ["user_id", "cookies"]
    for key in str_keys:
        if type(config[key]) != str:
            print("配置项 {} 应为str类型，程序退出".format(key))
            return 1
    if type(config["additional_user_ids"]) != list:
        print("配置项 additional_user_ids 应为list类型，程序退出")
        return 1
    time_keys = ["start_time", "stop_time", "update_start_time"]
    for key in time_keys:
        value_type = type(config[key])
        if value_type != int and value_type != str:
            print('配置项 {} 应为int，或格式为"%Y-%m-%d %H:%M"的str，或空白str,程序退出'.format(key))
            return 1
        if value_type == str:
            # 字符串非空
            if config[key]:
                time_patten = "%Y-%m-%d %H:%M"
                try:
                    time.strptime(config[key], time_patten)
                except:
                    print("配置项 {} 日期格式错误".format(key))
                    return 1

    print("检查配置项兼容")
    # 自动获取新微博和更新模式冲突
    if config["auto_get_increment"] and config["update_mode"]:
        print("配置项 auto_get_increment 和 update_mode 不能同时启动，程序退出")
        return 1
    # 更新模式必须有更新时间参数
    if config["update_mode"] and not config["update_start_time"]:
        print("update_mode 需指定 update_start_time，程序退出")
        return 1

    print("配置检查完成")
    return 0


def timestamp_to_str(timestamp):
    time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(timestamp / 1000))

    return time_str


if __name__ == '__main__':
    window = tk.Tk()
    window.geometry('10x10+2000+400')
    info = """
            该程序由唐文编写
            程序源码已上传到github，链接：https://github.com/IshtarTang/weibo_spider
            作者联系方式：
                微博：@唐文_Ishtar
                邮箱：18975585675@163.com
            评论更新和存储到mysql的功能未完成，近期内应该不会有空
            程序卡住了可以直接关闭然后重新启动，会从上次的进度开始运行
            
            不得以任何形式使用该程序获利
            
            按'是'以开始运行本程序，或按'否'退出
            
    """

    tmp_str = messagebox.askquestion("提示信息", info)

    window.destroy()
    if tmp_str == "no":
        print("程序退出")
        time.sleep(3)
        exit()
    config_filename = "./config.json"
    schedule_filename_base = "./{}/schedule.json"
    download_filename_base = "./{}/download.json"
    result_filename_base = "./{}/result.json"
    r_result_filename_base = "./{}/r_result.json"

    if check_config_file(config_filename):
        time.sleep(3)
        exit()
    config = read_json(config_filename)

    # 请求用的session
    session = requests.session()
    session.headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36"}
    cookies_str = config["cookies"]
    cookies = CookiestoDic(cookies_str)
    session.cookies.update(cookies)

    # 存储文件名
    print("获取用户标识")
    user_ident = get_user_ident(config, session)
    # 有指定时间时，文件夹名会带时间
    if config["stop_time"] or (
            config["start_time"] and not config["auto_get_increment"] and not config["update_mode"]):
        stop_time = config["stop_time"] if config["stop_time"] else "x"
        start_time = config["start_time"] if config["start_time"] else "x"
        if type(start_time) == int:
            start_time = timestamp_to_str(start_time)
        if type(stop_time) == int:
            stop_time = timestamp_to_str(stop_time)
        stop_time = stop_time.replace(":", "：")
        start_time = start_time.replace(":", "：")
        user_ident = user_ident + " ({}-{})".format(start_time, stop_time)
    schedule_filename = schedule_filename_base.format(user_ident)
    download_filename = download_filename_base.format(user_ident)
    result_filename = result_filename_base.format(user_ident)
    r_result_filename = r_result_filename_base.format(user_ident)

    check_run_file(user_ident, schedule_filename, download_filename, result_filename, r_result_filename)
    schedule = read_json(schedule_filename)

    # auto_get_increment：自动获取上次获取的最后一条时间戳
    if config["auto_get_increment"] and schedule["downloaded"] == 0:
        print("自动获取新微博已打开")
        saved_divs = read_json(result_filename)
        if saved_divs:
            if saved_divs[-1]["content"].strip().split("\n")[0] == "置顶":
                last_timestamp = saved_divs[-2]["public_timestamp"]
            else:
                last_timestamp = saved_divs[-1]["public_timestamp"]
        else:
            last_timestamp = 0
        config["start_time"] = last_timestamp
        config["stop_time"] = ""
        update_json_file(config, config_filename)
        print("已自动获取到上次保存的最后一条，时间为 {}".format(timestamp_to_str(last_timestamp)))
        # 清空上次的下载文件
        if schedule["downloaded"] == 0:
            update_json_file([], download_filename)
            print("已清除上次的下载文件")

    # 启动了更新模式，且进度为0
    if config["update_mode"] and schedule["downloaded"]:
        print("更新模式已打开")
        update_start_time = config["update_start_time"]
        saved_divs = read_json(result_filename)

        for div in saved_divs:
            # saved_divs为从早到晚，start_time 比 div的时间早时，截断
            if not is_b_later_than_a(div["public_timestamp"], update_start_time):
                saved_divs = saved_divs[:saved_divs.index(div) + 1]
                break
        input_str = input("确认删除result.json {} 之后文件(输入 yes 确认，或其他以退出)\n".format(config["update_start_time"]))
        if input_str == "yes":
            update_json_file(saved_divs, result_filename)
            print("已删除 {} 之后的微博文件".format(config["update_start_time"]))
        else:
            print("程序退出")
            print("窗口将于3秒后关闭")
            time.sleep(3)
            exit()
    print("--------------------------------------------------------------------")
    is_on = lambda x: "on" if x > 0 else "off"
    print_str_base = """
要爬取的主页为：{}
文件标识：{} 
获取当该用户全部评论：{}
其他需获取全部评论的用户id：{}

自动获取新微博：{}
爬取时间范围为：{}

更新模式：{}
更新时间范围：{}
"""
    # 提示输出
    # 主页链接
    main_url = "https://weibo.com/" + config["user_id"]
    # 获取所有评论
    get_all_comment_str = is_on(config["get_all_comment"])
    # 其他需获取全部评论的用户id
    if config["get_all_comment"]:
        if config["additional_user_ids"]:
            additional_user_ids = ",".join(config["additional_user_ids"])
        else:
            additional_user_ids = "无"
    else:
        additional_user_ids = "/"
    # 时间范围
    stop_time = ""
    if not (config["start_time"] or config["stop_time"]):
        time_range = "所有"
    else:
        start_time = config["start_time"] if config["start_time"] else "x"
        start_time = start_time if type(start_time) == str else timestamp_to_str(start_time)
        stop_time = config["stop_time"] if config["stop_time"] else "x"
        stop_time = stop_time if type(stop_time) == str else timestamp_to_str(stop_time)
        time_range = "{} - {}".format(start_time, stop_time)
    # 自动获取新微博
    auto_get_increment_str = is_on(config["auto_get_increment"])
    update_mode_str = is_on(config["update_mode"])
    if config["update_mode"]:
        update_start_time = config["update_start_time"]
        update_start_time = update_start_time if type(update_start_time) else timestamp_to_str(update_start_time)
        update_time_range = "{} - {}".format(update_start_time, stop_time)
    else:
        update_time_range = "/"

    print_str = print_str_base.format(main_url, user_ident, get_all_comment_str, additional_user_ids,
                                      auto_get_increment_str, time_range, update_mode_str, update_time_range)
    print(print_str)
    if not input("输入ok以继续\n") == "ok":
        print("程序退出")

    """
    ----------------程序运行----------------------
    """
    try:
        # 下载div文件
        if schedule["downloaded"] != "done":
            print("开始下载")
            download_weibo_file(config, session, schedule_filename, download_filename)
        else:
            print("下载已在之前的运行中结束，进入解析")

        # 解析
        weibo_divs = read_json(download_filename)
        if schedule["parsed"] != "done":
            parse_weibo(session, weibo_divs, config, schedule_filename, result_filename)
        else:
            print("解析已在之前的运行中结束，程序结束")
        print("要进自动获取新微博或更新 请删除schedule.json")
        time.sleep(5)
    except:
        traceback.print_exc()
        print('traceback.format_exc():\n%s' % traceback.format_exc())
        print("异常中断，尝试重启程序，重启还不行就是真的有问题")
        print("窗口将于10秒后关闭")
        time.sleep(10)
