class ArchiveProtectionMixin:
    def validate(self, attrs):
        instance: Archivable = self.instance  # type:ignore
        if instance and (instance.is_archived or instance.is_deleted):
            raise ValueError("Cannot modify an archived or deleted item")
        return super().validate(attrs)  # type:ignore
