from models.setting import Setting

KEY_IAM_PERMISSIONS = 'IAM_PERMISSIONS'


class SettingsService:

    @staticmethod
    def get_all_settings():
        return list(Setting.scan())

    @staticmethod
    def create(name, value):
        return Setting(name=name, value=value)

    @staticmethod
    def get(name):
        setting = Setting.get_nullable(hash_key=name)
        if setting:
            return setting.value

    @staticmethod
    def delete(name):
        setting = Setting.get_nullable(hash_key=name)
        if setting:
            setting.delete()

    @staticmethod
    def save(setting: Setting):
        return setting.save()

    @staticmethod
    def get_iam_permissions():
        return SettingsService.get(name=KEY_IAM_PERMISSIONS)
