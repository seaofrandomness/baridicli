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
            self.session.cookies.set("BrowserTimezone", "GMT+01:00")
            return True
        else:
            return False

    def accounts(self):
        resp = self.session.get(f"{self.domain}/rb/web/pages/accounts.xhtml")
        self.rip = findall(r"class=\"link\s*text text--h4-header\s*\">(\d{20})", resp.text)[0]
        balance = findall(r"<div class=\"dir-ltr\">(.*\.\d{2}\s*DZD)", resp.text)[0]
        return (self.rip, balance)

    def generate_transfer_data(self, source: str, render: str, additional_fields: dict):
        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': source,
            'javax.faces.partial.execute': '@all',
            'javax.faces.partial.render': render,
            'javax.faces.ViewState': self.view_state,
        }
        data.update(additional_fields)
        return data

    def transfer(self, rip_dest: str, amount: str):
        resp = self.session.get(f"{self.domain}/rb/web/pages/transfers.xhtml")
        j_idt = findall(r'<a id="transferTypesForm:(j_idt\d+)"', resp.text)[0]

        # First POST request
        data = self.generate_transfer_data(
            source=f'transferTypesForm:{j_idt}',
            render='transfersForm transferTypesForm',
            additional_fields={
                f'transferTypesForm:{j_idt}': f'transferTypesForm:{j_idt}',
                'transferTypesForm': 'transferTypesForm'
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/transfers.xhtml", data=data)

        j_idt_1 = findall(r'<script id="transfersForm:(j_idt\d+)"', resp.text)[0]
        j_idt_2 = findall(r'<button id="transfersForm:(j_idt\d+)"', resp.text)[0]

        # Second POST request
        common_data = {
            'transfersForm': 'transfersForm',
            'transfersForm:sourcesMenu_focus': '',
            'transfersForm:sourcesMenu_input': self.rip,
            'transfersForm:externalCardDetail:cardParametersForm': 'transfersForm:externalCardDetail:cardParametersForm',
            'transfersForm:targetOtherCardAccount': rip_dest,
            'transfersForm:paymentAmount_input': str(float(amount)),
        }

        data = self.generate_transfer_data(
            source=f'transfersForm:{j_idt_2}',
            render='transfersForm',
            additional_fields={
                **common_data,
                f'transfersForm:{j_idt_2}': f'transfersForm:{j_idt_2}',
                'transfersForm:paymentAmount_hinput': amount
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/transfers.xhtml", data=data)

        j_idt_1, j_idt_2 = findall(r'<a id="transfersForm:(j_idt\d+):(j_idt\d+)"', resp.text)[0]
        j_idt_3 = findall(r'<button id="transfersForm:(j_idt\d+)"', resp.text)[0]

        # Third POST request
        data = self.generate_transfer_data(
            source=f'transfersForm:{j_idt_2}',
            render='transfersForm',
            additional_fields={
                **common_data,
                f'transfersForm:{j_idt_1}:{j_idt_2}': f'transfersForm:{j_idt_1}:{j_idt_2}',
                f'transfersForm:{j_idt_1}:oneTimePasswordConf': ''
            }
        )

        # Confirm the transfer
        otp_code = input('Enter the OTP: ')

        data = self.generate_transfer_data(
            source=f'transfersForm:{j_idt_3}',
            render='transfersForm transferTypesForm transfersForm:operationActionGroup',
            additional_fields={
                **common_data,
                f'transfersForm:{j_idt_3}': f'transfersForm:{j_idt_3}',
                f'transfersForm:{j_idt_1}:oneTimePasswordConf': otp_code,
                'transfersForm:paymentAmount_hinput': amount
            }
        )

        resp = self.session.post(f"{self.domain}/rb/web/pages/transfers.xhtml", data=data)

        success_strings = [
            'تمت العملية',
            'Transfer done. Thank you!',
        ]

        if any(substring in resp.text for substring in success_strings):
            print('Transfer successful.')
        else:
            print('Failed to transfer.')


    def verify_phone(self, phone:str):
        if len(phone) == 10 and phone.isdigit():
            if phone[:2] == '05':
                return 0 # ooredoo
            elif phone[:2] == '06':
                return 1 # mobilis
            elif phone[:2] == '07':
                return 2 # djezzy

        raise ValueError("--phone must be a valid 10 digits phone number.")


    def flexy(self, phone: str, amount: str):
        operator = self.verify_phone(phone)
        phone = f'213{phone[1:]}'
        resp = self.session.get(f"{self.domain}/rb/web/pages/payments.xhtml")
        j_idt_1 = findall(r'<a id="paymentsForm:(j_idt\d+:\d:j_idt\d+)"', resp.text)[0]
        j_idt_2 = findall(r'<div id="paymentsForm:(j_idt\d+)"', resp.text)[0]

        # First POST request
        data = self.generate_transfer_data(
            source=f'paymentsForm:{j_idt_1}',
            render='paymentsForm',
            additional_fields={
                'javax.faces.partial.execute': f'paymentsForm:{j_idt_1}',
                'primefaces.resetvalues': 'true',
                'javax.faces.behavior.event':'click',
                'javax.faces.partial.event':'click',
                'paymentsForm': 'paymentsForm',
                f'payments:{j_idt_2}:regions_focus': '',
                f'paymentsForm:{j_idt_2}:filterAllProviderValue':'',
                f'paymentsForm:{j_idt_2}_active': '-1',
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/payments.xhtml", data=data)

        # Second POST request
        data = self.generate_transfer_data(
            source=f'paymentsForm:{j_idt_1}',
            render='paymentsForm',
            additional_fields={
                'javax.faces.behavior.event':'click',
                'javax.faces.partial.event':'click',
                'paymentsForm': 'paymentsForm',
                f'payments:{j_idt_2}:regions_focus': '',
                f'paymentsForm:{j_idt_2}:filterAllProviderValue':'',
                f'paymentsForm:{j_idt_2}_active': '-1',
                f'paymentsForm:{j_idt_1}': f'paymentsForm:{j_idt_1}',
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/payments.xhtml", data=data)
        j_idt_3 = findall(r'<a id="paymentsForm:(j_idt\d+:\d:j_idt\d+)"', resp.text)[operator]
        j_idt_4 = findall(r'<div id="paymentsForm:(j_idt\d+)"', resp.text)[0]

        # Third POST request
        data = self.generate_transfer_data(
            source=f'paymentsForm:{j_idt_3}',
            render='paymentsForm',
            additional_fields={
                'paymentsForm': 'paymentsForm',
                f'paymentsForm:{j_idt_3}': f'paymentsForm:{j_idt_3}',
                f'paymentsForm:{j_idt_4}:regionList_focus': '',
                f'paymentsForm:{j_idt_4}:filterProviderValue':'',
                f'paymentsForm:{j_idt_4}_active': '-1',
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/payments.xhtml", data=data)
        j_idt_5 = findall(r'<button id="paymentsForm:(j_idt\d+)"', resp.text)[0]
        j_idt_6 = findall(r'for="paymentsForm:(j_idt\d+:\d:)phoneField"', resp.text)[0]
        source = findall(r'<option value="(\b\d{16}\b)"', resp.text)[0]

        # Fourth POST request
        data = self.generate_transfer_data(
            source=f'paymentsForm:{j_idt_5}',
            render='paymentsForm',
            additional_fields={
                'paymentsForm': 'paymentsForm',
                f'paymentsForm:{j_idt_5}': f'paymentsForm:{j_idt_5}',
                'paymentsForm:sourcesMenu_focus': '',
                'paymentsForm:sourcesMenu_input': source,
                'paymentsForm:paymentExternalCardDetail:cardParametersForm': 'paymentsForm:paymentExternalCardDetail:cardParametersForm',
                'paymentsForm:paymentAmount_input': f'{amount}.00',
                'paymentsForm:paymentAmount_hinput': amount,
                f'paymentsForm:{j_idt_6}phoneField': phone,
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/payments.xhtml", data=data)
        j_idt_7 = findall(r'<button id="paymentsForm:(j_idt\d+)"', resp.text)[0]
        j_idt_8 = findall(r'for="paymentsForm:(j_idt\d+):oneTimePasswordConf"', resp.text)[0]

        # Confirm the flexy operation
        otp_code = input('Enter the OTP: ')

        data = self.generate_transfer_data(
            source=f'paymentsForm:{j_idt_7}',
            render='paymentsForm',
            additional_fields={
                'paymentsForm': 'paymentsForm',
                f'paymentsForm:{j_idt_7}': f'paymentsForm:{j_idt_7}',
                'paymentsForm:sourcesMenu_focus': '',
                'paymentsForm:sourcesMenu_input': source,
                'paymentsForm:paymentExternalCardDetail:cardParametersForm': 'paymentsForm:paymentExternalCardDetail:cardParametersForm',
                'paymentsForm:paymentAmount_input': f'{amount}.00',
                'paymentsForm:paymentAmount_hinput': amount,
                f'paymentsForm:{j_idt_6}phoneField': phone,
                f'paymentsForm:{j_idt_8}:oneTimePasswordConf': {otp_code},
            }
        )
        resp = self.session.post(f"{self.domain}/rb/web/pages/payments.xhtml", data=data)

        success_strings = [
            'تمت عملية الدفع',
            'Payment done.',
        ]

        if any(substring in resp.text for substring in success_strings):
            print('Flexy operation successful.')
        else:
            print('Flexy operation failed.')
