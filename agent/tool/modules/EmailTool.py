import smtplib
# 负责构造文本
from email.mime.text import MIMEText
# 负责构造图片
from email.mime.image import MIMEImage
# 负责将多个对象集合起来
from email.mime.multipart import MIMEMultipart
from email.header import Header
from agent.AgentGraph import Node
import json
from agent.model.BaseModel import BaseModel
import config

# SMTP服务器,这里使用163邮箱
mail_host = config.MAIL_HOST
# 发件人邮箱
mail_sender = config.MAIL_SNDDER
# 邮箱授权码,注意这里不是邮箱密码,如何获取邮箱授权码,请看本文最后教程
mail_license = config.MAIL_LICENSE
smtp_port = config.MAIL_PORT

class EmailTool(Node):

    def getPrompt(self):
          content = """
          你是一名邮件发送助手，可以使用已有工具解决问题。以下是你的工作职责和任务描述:
          1. 提取收件人邮箱、邮件主题、邮件内容并使用工具发送邮件。
          2. 如果没有提取到邮件内容，可以根据上下文用户意图生成邮件内容
          3. 如果邮件主题缺失，可以从邮件内容中生成邮件主题。
          
          返回json格式:
          {"status": <int>,"reply": <string>,"tool_use": <bool>,"tool_name": <string>,"args": <list>}
          
          返回值说明:
          - `status`：0 -> 收件人邮箱或邮件主题或邮件内容信息却失，需要用户补充, 2 -> 执行成功
          - `reply`: `status` 为 2 -> 提供问题解决信息， `status` 为 0 -> 需要补充的信息 
          - `tool_use`:  true -> 需使用工具, false -> 不使用工具
          - `tool_name`: 使用的工具名称
          - `args`: 工具所需的参数列表
          
          已有工具信息:
          - `send(receivers: str, subject: str, content: str)`: 发送邮件
            - `receivers`: 描述 -> 接收人邮箱，多个用逗号分隔； 验证 -> 不能为空，符合邮件格式
            - `subject`: 描述 -> 邮件主题； 验证 -> 不能为空
            - `content`: 描述 -> 邮件内容； 验证 -> 不能为空
    
          """
          message = {"role": "system", "content": content}
          return message

    def queryDesc(self) -> str:
        desc = """
        EmailTool -> 这是一名邮件发送助手Agent，可以使用的工具如下:
            - `send(receivers: str, subject: str, content: str)`: 立即发送邮件
                - `receivers`:  描述 -> 接收人邮箱，多个用逗号分隔； 验证 -> 不能为空，符合邮件格式
                - `subject`: 描述 -> 邮件主题； 验证 -> 不能为空
                - `content`: 描述 -> 邮件内容； 验证 -> 不能为空
        """
        return desc

    def queryName(self) -> str:
        return "EmailTool"

    async def exec(self, messageNo: str,llm: BaseModel) -> str:
        response = await llm.acall(json.dumps(self.messageDict[messageNo]))
        jsonData = json.loads(response)

        if jsonData["status"] == 2:
            try:
                getattr(self, jsonData["tool_name"])(*jsonData["args"])
            except Exception as e:
                print(f"错误: {e}")
                jsonData["reply"] = "邮件发送失败"

        self.reply = jsonData["reply"]
        self.appendMessage(messageNo, {"role": "assistant", "content": self.reply})

        return json.dumps(jsonData)

    def send(self,receivers: str, subject: str, content: str):
        mm = MIMEMultipart('related')
        mail_receivers = receivers

        # 设置发送者,注意严格遵守格式,里面邮箱为发件人邮箱
        mm["From"] = mail_sender
        # 设置接受者,注意严格遵守格式,里面邮箱为接受者邮箱
        mm["To"] = receivers
        # 设置邮件主题
        mm["Subject"] = Header(subject, 'utf-8')
        # 构造文本,参数1：正文内容，参数2：文本格式，参数3：编码方式
        message_text = MIMEText(content, "plain", "utf-8")
        # 向MIMEMultipart对象中添加文本对象
        mm.attach(message_text)
        stp = smtplib.SMTP(mail_host, smtp_port)

        stp.starttls()
        # set_debuglevel(1)可以打印出和SMTP服务器交互的所有信息
        stp.set_debuglevel(1)
        # 登录邮箱，传递参数1：邮箱地址，参数2：邮箱授权码
        stp.login(mail_sender, mail_license)
        # 发送邮件，传递参数1：发件人邮箱地址，参数2：收件人邮箱地址，参数3：把邮件内容格式改为str
        stp.sendmail(mail_sender, mail_receivers, mm.as_string())  # 创建SMTP对象

        stp.quit()

instance = EmailTool()