"""
UI Factory for creating different display types
"""

from typing import Any

from rich.console import Console

from ..exceptions import UILoadError
from .base import BaseUIDisplay


class UIFactory:
    """Factory for creating UI display instances"""

    _displays: dict[str, type[BaseUIDisplay]] = {}

    @classmethod
    def register(cls, name: str, display_class: type[BaseUIDisplay]) -> None:
        """Register a UI display type"""
        cls._displays[name] = display_class

    @classmethod
    def create(
        cls,
        display_type: str,
        console: Console | None = None,
        config: Any | None = None,
        **kwargs: Any,
    ) -> BaseUIDisplay:
        """
        Create a UI display instance

        Args:
            display_type: Type of display ('tqdm', 'simple', 'alive', 'textual', 'rich')
            console: Optional Rich Console instance.
            config: Optional configuration object
            **kwargs: Additional arguments for the display class

        Returns:
            BaseUIDisplay instance
        """
        if display_type not in cls._displays:
            available = list(cls._displays.keys())
            raise UILoadError(
                f"Unknown display type '{display_type}'. Available: {available}",
                ui_type=display_type,
                fallback_available=len(available) > 0,
            )

        display_class = cls._displays[display_type]
        console_instance = console or Console()

        # Build constructor arguments with proper parameter filtering
        import inspect

        init_kwargs = {}

        try:
            sig = inspect.signature(display_class.__init__)
            valid_params = set(sig.parameters.keys())

            # Add console if the constructor accepts it
            if "console" in valid_params:
                init_kwargs["console"] = console_instance

            # Add config if the constructor accepts it
            if config is not None and "config" in valid_params:
                init_kwargs["config"] = config

            # Add only the kwargs that the constructor accepts
            for key, value in kwargs.items():
                if key in valid_params:
                    init_kwargs[key] = value
        except Exception:
            # Fallback: minimal safe parameters
            init_kwargs = {"console": console_instance}
            if config is not None:
                init_kwargs["config"] = config

        return display_class(**init_kwargs)

    @classmethod
    def available_displays(cls) -> list[str]:
        """Get list of available display types"""
        return list(cls._displays.keys())

    @classmethod
    def get_default(
        cls, console: Any | None = None, config: Any | None = None
    ) -> BaseUIDisplay:
        """Get default UI display (TQDM if available, otherwise Simple)"""
        try:
            return cls.create("tqdm", console=console, config=config)
        except (UILoadError, ImportError):
            try:
                return cls.create("simple", console=console, config=config)
            except (UILoadError, ImportError):
                raise UILoadError(
                    "No UI displays available",
                    ui_type="default",
                    fallback_available=False,
                )


def auto_register_displays() -> None:
    """Automatically register all available display types"""

    # Try to register TQDM display
    # Try to register TQDM display
    try:
        from .displays.tqdm_display import TQDMDisplay

        UIFactory.register("tqdm", TQDMDisplay)  # type: ignore
    except ImportError:
        pass

    # Try to register Simple display
    try:
        from .displays.simple_display import SimpleDisplay

        UIFactory.register("simple", SimpleDisplay)
    except ImportError:
        pass

    # Try to register Simple Clean display (for UI A mode)
    try:
        from .displays.simple_clean_display import SimpleCleanDisplay

        UIFactory.register("simple_clean", SimpleCleanDisplay)
    except ImportError:
        pass

    # Try to register Alive-Progress display
    try:
        from .displays.alive_display import AliveDisplay

        UIFactory.register("alive", AliveDisplay)
    except ImportError:
        pass

    # Try to register Textual display
    try:
        from .displays.textual_display import TextualDisplay

        UIFactory.register("textual", TextualDisplay)
    except ImportError:
        pass

    # Try to register Rich display (existing)
    try:
        from .displays.rich_display import RichDisplay

        UIFactory.register("rich", RichDisplay)
    except ImportError:
        pass


# Auto-register displays when module is imported
auto_register_displays()
