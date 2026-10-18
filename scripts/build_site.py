#!/usr/bin/env python3
"""Compatibility entry point for the componentized public-site build."""
from render_site import PUBLIC_FILES, build, main, safe_destination, validate_sources

if __name__ == '__main__':
    main()
