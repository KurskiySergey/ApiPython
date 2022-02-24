import requests
import json
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

    @staticmethod
    def _save_info(name, info):
        with open(name, 'w', encoding='utf-8') as save_file:
            try:
                json.dump(info, save_file)
            except json.JSONDecodeError:
                save_file.write(info)

    def show_user_repos(self, username=None, auth=False, save=True):
        user_repos = self._get_repos_list(username=username, auth=auth)
        user = self.username if username is None else username
        print(f"Список репозиториев пользователя {user}")
        if save:
            GitHubApi._save_info(f"{user}_repos.json", user_repos)
        pprint(user_repos)

    def show_user_info(self, username=None, auth=False, save=True):
        info = self._get_user(username=username, auth=auth)
        user = info.get('login')
        print(f"Информация о пользователе {user}")
        if save:
            GitHubApi._save_info(f"{user}.json", info)
        pprint(info)


if __name__ == "__main__":
    login = "KurskiySergey"
    access_token = "access_token"
    api = GitHubApi(username=login, token=access_token)
    api.show_user_info(auth=False, save=True)
    api.show_user_repos(auth=False, save=True)
