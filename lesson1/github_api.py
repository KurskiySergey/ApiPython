import requests
from pprint import pprint


class GitHubApi:
    def __init__(self, username=None, token=None):
        self.username = username
        self.__token = token
        self.__auth_header = {"Authorization": f"token {self.__token}"}

    @staticmethod
    def hello_world():
        api_url = "https://api.github.com/zen"
        response = requests.get(api_url)
        return response.text

    def _get_user(self, username=None, auth=False):
        if auth:
            headers = self.__auth_header
            api_url = f"https://api.github.com/user"
        else:
            headers = {}
            api_url = f"https://api.github.com/users/{self.username if username is None else username}"
        try:
            response = requests.get(api_url, headers=headers)
            result = response.json()
        except Exception:
            result = {"Возникла ошибка"}
        return result

    def _get_repos_list(self, username=None, auth=False):
        if auth:
            headers = self.__auth_header
            api_url = f"https://api.github.com/user/repos"
        else:
            headers = {}
            api_url = f"https://api.github.com/users/{self.username if username is None else username}/repos"

        try:
            response = requests.get(api_url, headers=headers).json()
            result = [f"{repository.get('name')} ({'private' if repository.get('private') else 'public'})" for repository in response]
        except Exception:
            result = ["Возникла ошибка"]

        return result

    def show_user_repos(self, username=None, auth=False):
        user_repos = self._get_repos_list(username=username, auth=auth)
        print(f"Список репозиториев пользователя {self.username if username is None else username}")
        pprint(user_repos)

    def show_user_info(self, username=None, auth=False):
        info = self._get_user(username=username, auth=auth)
        print(f"Информация о пользователе {info.get('login')}")
        pprint(info)


if __name__ == "__main__":
    login = "KurskiySergey"
    access_token = "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"
    api = GitHubApi(username=login, token=access_token)
    api.show_user_info(auth=True)
    api.show_user_repos(auth=True)
