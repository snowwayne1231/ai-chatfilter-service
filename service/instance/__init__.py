from service.main import MainService



class MemoryController(object):
    """

    """

    main_service = None

    def __init__(self):
        pass
        

    def get_main_service(self, is_admin = False):
        if self.main_service is None:
            self.main_service = MainService(is_admin)

        return self.main_service



mc = MemoryController()

get_main_service = mc.get_main_service