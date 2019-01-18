from passrotate.provider import Provider, ProviderOption, PromptType, register_provider
from passrotate.forms import get_form
from bs4 import BeautifulSoup
import requests


class CasUTC(Provider):
    """
    [cas.utc.fr]
    username=Your CAS username
    """
    name = "UTC CAS"
    domains = [
        "utc.fr",
        "cas.utc.fr",
        "ent.utc.fr"
    ]
    options = {
        "username": ProviderOption(str, "Your CAS username")
    }

    def __init__(self, options):
        self.username = options["username"]

    def prepare(self, old_password):
        self._session = requests.Session()
        r = self._session.get("https://cas.utc.fr/cas/login")
        form = get_form(r.text, id="fm1")
        form.update({
            "username": self.username,
            "password": old_password,
        })

        r = self._session.post("https://cas.utc.fr/cas/login", data=form)

        soup = BeautifulSoup(r.text, "html.parser")
        err = soup.find(id="error_general")
        if err and "Invalid" in err.find("span").text:
            raise Exception("Unable to log into CAS with your current password")
        elif err:
            raise Exception("Unable to log into CAS : unknown exception")

        r = self._session.get('https://comptes.utc.fr/accounts-web/tools/changePassword.xhtml')
        self._form = get_form(r.text, id="form")

    def execute(self, old_password, new_password):
        self._form.update({
            "pwd1": new_password,
            "pwd2": new_password,
            "javax.faces.partial.ajax": "true",
            "javax.faces.source": "j_idt30",
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "form",
            "j_idt30": "j_idt30"
        })

        r = self._session.post("https://comptes.utc.fr/accounts-web/tools/changePassword.xhtml",
                               data=self._form,
                               headers={
                                   "origin": "https://comptes.utc.fr",
                                   "referer": "https://comptes.utc.fr/accounts-web/tools/changePassword.xhtml",
                                   "Faces-Request": "partial/ajax",
                                   "X-Requested-With": "XMLHttpRequest"
                               }
                               )

        soup = BeautifulSoup(r.text, features="html5lib")
        err = soup.find("div", {"class": "ui-messages-error"})
        if err:
            raise Exception("Unable to change password for CAS : \n" + '\n'.join([e.text for e in err.findAll("span")]))


register_provider(CasUTC)
