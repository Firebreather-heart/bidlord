from django.db.models import FileField


class BaseSizeAdapter:
    def get_size(self, file_field)->int:
        """
            Return the file size in bytes
            must be implemented by all adapters
        """
        raise NotImplementedError
    


class LocalStorageSizeAdapter(BaseSizeAdapter):
    def get_size(self, file_field) -> int:
        return file_field.size #type:ignore
    

def get_size_adapter(storage_backend) -> BaseSizeAdapter:
    backend_class = storage_backend.__class__.__name__

    if backend_class == 'FileSystemStorage':
        return LocalStorageSizeAdapter()
    # implement the rest later
    raise ValueError(f"No size adapter found for backend {backend_class}")