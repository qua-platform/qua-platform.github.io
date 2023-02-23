import pretty_errors

pretty_errors.configure(
    filename_display=pretty_errors.FILENAME_COMPACT, display_arrow=True
)


def disable_colored_errors():
    """Disables the colors in the error output, used for terminals that does not support coloring,
    such as powershell, cmder, and other physical terminals.
    """
    pretty_errors.mono()


def activate_verbose_errors():
    """Adds advance debug information to the error output, useful for debugging."""
    pretty_errors.configure(
        filename_display=pretty_errors.FILENAME_FULL,
        lines_before=5,
        lines_after=2,
        trace_lines_before=5,
        trace_lines_after=2,
        display_locals=True,
        display_trace_locals=True,
    )
