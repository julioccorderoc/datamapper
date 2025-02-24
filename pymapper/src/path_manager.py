from contextlib import contextmanager

# convertir el validador de path a un booleano
class DynamicPathManager:
    """
    Handles dynamic path tracking during mapping operations.
    Maintains separate path stacks that can be created on demand for different path types.
    Each path includes its main model name and current path segments.
    
    Example paths:
        - CustomModel.field_name
        - AnotherModel.nested.field.path
        - SourceModel.list_field[0].nested_field
    """
    
    _instance = None
    
    def __new__(cls, *path_configs: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(*path_configs)  # Llamar a un inicializador interno
        return cls._instance
    
    def __init__(self, *path_configs: str):
        """
        Initialize path trackers with path types and their model names.
        
        Args:
            *path_configs: Variable number of strings contaning the path identifiers
        
        Example:
            >>> tracker = PathTracker(("source", "UserModel"), ("target", "ProfileModel"))
            >>> tracker = PathTracker(
            ...     ("input", "RequestModel"), 
            ...     ("output", "ResponseModel"), 
            ...     ("intermediate", "ProcessModel")
            ... )
        """
        self._path_registry = {}
        for path_identifier in path_configs:
            self.create_path_type(path_identifier)

    def create_path_type(self, path_identifier: str) -> None:
        """
        Args:
            path_identifier: Identifier for the new path type

        Raises:
            ValueError: If path_identifier already exists
            
        Example:
            >>> tracker.create_path_type("validation", "ValidationModel")
        """
        if path_identifier in self._path_registry:
            raise ValueError(f"Path type already exists: {path_identifier}")
            
        self._path_registry[path_identifier] = {"segments": []}
    
    @contextmanager
    def track_segment(self, path_identifier: str, segment: str):
        """
        Context manager for tracking path segments for any path type.
        
        Args:
            path_identifier: Identifier for the path type
            segment: Path segment to append (e.g., "field_name" or "[0]")
            
        Raises:
            ValueError: If path_identifier is not recognized or trying to add list index without a preceding segment
                       
        Example:
            >>> with tracker.track_segment("source", "user"):
            >>>     with tracker.track_segment("source", "[0]"):
            >>>         # Path will be "SourceModel.user[0]"
        """
        self._is_valid_path(path_identifier)
        segments = self._path_registry[path_identifier]["segments"]
        
        if segment.startswith("[") and segment.endswith("]"):
            if not segments:
                raise ValueError(f"Cannot add list index {segment} without a preceding segment for {path_identifier} path.")
            segments[-1] += segment
        else:
            segments.append(segment)
            
        try:
            yield
        finally:
            if segments:
                if segment.startswith("[") and segment.endswith("]"):
                    # Remove the index from the last segment
                    segments[-1] = segments[-1][:-len(segment)]
                else:
                    segments.pop()
    
    def get_path(self, path_identifier: str) -> str:
        """
        Get the full path for a specific path type, including the model name.
        
        Args:
            path_identifier: Identifier for the path type
            
        Returns:
            str: Full path including model name and all segments
            
        Raises:
            ValueError: If path_identifier is not recognized
        """
        self._is_valid_path(path_identifier)
        segments = self._path_registry[path_identifier]["segments"]
        return ".".join(segments) if segments else ""
    
    def _is_valid_path(self, path_identifier: str) -> None:
        """
        Validate that a path type exists in the tracker.
        
        Args:
            path_identifier: Identifier to validate
            
        Raises:
            ValueError: If path_identifier is not recognized
        """
        if path_identifier not in self._path_registry:
            raise ValueError(f"Unknown path type: '{path_identifier}'. Available types: {list(self._path_registry.keys())}")
            
    def list_path_types(self) -> list[str]:
        """
        Returns:
            list[str]: List of path type identifiers
        """
        return list(self._path_registry.keys())