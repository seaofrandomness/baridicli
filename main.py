from dotenv import dotenv_values
from requests import session
from re import findall


class Baridi:
    def __init__(self):
        self.domain = "https://baridiweb.poste.dz/"
        self.credentials = dotenv_values(".env")
        self.session = session()
        self.session.headers.update({
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": "\"Not-A.Brand\";v=\"99\", \"Chromium\";v=\"124\"",
            "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": "\"Linux\"",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.118 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Priority": "u=0, i",
            "Connection": "keep-alive"
        })
        response = self.session.get(self.domain)
        regex = r"id=\"javax\.faces\.ViewState\"\svalue=\"(.*?)\""
        self.view_state = findall(regex, response.text)[0]

    def login(self):
        resp = self.session.post(
            f"{self.domain}/rb/web/pages/login.xhtml",
            data={
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": "loginForm:loginButton",
                "javax.faces.partial.execute": "@all",
                "javax.faces.partial.render": "loginForm",
                "loginForm:loginButton": "loginForm:loginButton",
                "loginForm": "loginForm",
                "loginForm:loginInput": self.credentials['USER'],
                "loginForm:passwordHashInput": self.credentials['PASS'],
                "noClientHashing": "false",
                "vCode": '',
                "javax.faces.ViewState": self.view_state
            }
        )
        if '<redirect url="/rb/web/pages/home.xhtml">' in resp.text:
            return True
        else:
            return False

    def accounts(self):
        self.session.cookies.set("BrowserTimezone", "GMT+01:00")
        resp = self.session.get(f"{self.domain}/rb/web/pages/accounts.xhtml")
        rip = findall(r"class=\"link\s*text text--h4-header\s*\">(\d{20})", resp.text)[0]
        balance = findall(r"<div class=\"dir-ltr\">(.*\.\d{2}\s*DZD)", resp.text)[0]
        return (rip, balance)


# testing
x = Baridi()
if x.login():
    print(x.accounts())