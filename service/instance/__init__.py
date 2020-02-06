from service.main import MainService



class MemoryController(object):
    """

    """

    main_service = None

    def __init__(self):
        pass
        

    def get_main_service(self):
        if self.main_service is None:
            self.main_service = MainService()

        return self.main_service



mc = MemoryController()

get_main_service = mc.get_main_service