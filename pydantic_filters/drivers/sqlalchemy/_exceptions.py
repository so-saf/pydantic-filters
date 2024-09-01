
class BaseSaDriverError(Exception):
    pass


class AttributeNotFoundSaDriverError(BaseSaDriverError):
    pass


class RelationshipNotFoundSaDriverError(BaseSaDriverError):
    pass
