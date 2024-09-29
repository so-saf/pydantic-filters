
class BaseSaDriverError(Exception):
    """Base SQLAlchemy driver error"""


class AttributeNotFoundSaDriverError(BaseSaDriverError):
    pass


class RelationshipNotFoundSaDriverError(BaseSaDriverError):
    pass


class SupportSaDriverError(BaseSaDriverError):
    """Driver support error"""
