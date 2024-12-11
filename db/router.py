class OtherRouter:
    """
    A router to control all database operations on models in the
    bstat applications.
    """

    route_app_labels = {"other"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read bstat models go to geek database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "other"
        return None

    def db_for_write(self, model, **hints):
        """
        Attempts to write bstat models go to geek database.
        """
        if model._meta.app_label in self.route_app_labels:
            return "other"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the bstat apps is
        involved.
        """
        if obj1._meta.app_label in self.route_app_labels or obj2._meta.app_label in self.route_app_labels:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Make sure the bstat apps only appear in the
        'sdk_stat' database.
        """
        if app_label in self.route_app_labels:
            return db == "other"
        return None
