"""
Define the base classes for the Sumatra version control abstraction layer.
"""

import os.path


class VersionControlError(Exception):
    pass

class UncommittedModificationsError(Exception):
    pass


class Repository(object):
    """
    Represents, and enables limited interaction with, the version control system
    repository located at *url*.
    
    If *upstream* is not provided, this information will be obtained, if
    possible, from the version control system.
    """
    
    def __init__(self, url, upstream=None):
        if url == ".":
            url = os.path.abspath(url)
        self.url = url
        self.upstream = upstream
        
    def __str__(self):
        s = "%s at %s" % (self.__class__.__name__, self.url)
        if self.upstream:
            s += " (upstream: %s)" % self.upstream
        return s
    
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.url == other.url
    
    def __ne__(self, other):
        return not self.__eq__(other)

    def __getstate__(self):
        """For pickling"""
        return {'url': self.url, 'upstream': self.upstream}

    def __setstate__(self, state):
        """For unpickling"""
        self.__init__(state['url'])
        self.upstream = state['upstream']

    @property
    def exists(self):
        """Does the repository represented by this object actually exist?"""
        raise NotImplementedError
    
    def checkout(self, path="."):
        """
        Clone a repository ("checkout" in Subversion) from *self.url* to
        the local filesystem at *path*.
        
        """
        raise NotImplementedError

    def get_working_copy(self, path=None):
        """
        Return a :class:`WorkingCopy` object corresponding to a checkout of this repository.
        """
        raise NotImplementedError



class WorkingCopy(object):
    """
    Represents, and enables limited interaction with, the version control system
    working copy located in the *path* directory.
    
    If *path* is not specified, the current working directory is assumed.
    
    For each version control system supported by Sumatra, there is a specific
    subclass of the abstract :class:`WorkingCopy` base class.
    """
    
    def __init__(self, path=None):
        self.path = path or os.getcwd()
    
    def __eq__(self, other):
        return (self.repository == other.repository) and (self.path == other.path) \
               and (self.current_version() == other.current_version()) #and (self.diff() == other.diff())
            
    def __ne__(self, other):
        return not self.__eq__(other)

    def contains(self, path):
        """
        Does the repository contain the file with the given path?
        
        where `path` is relative to the working copy root.
        """
        status = self.status()    
        return (path in status['modified']) or (path in status['clean'])

    def current_version(self):
        """Return the version of the current state of the working copy."""
        raise NotImplementedError

    def use_version(self, version):
        """
        Switch the working copy to *version*.
        
        If the working copy has uncommitted changes, raises an
        :class:`UncommittedModificationsError`.
        """
        raise NotImplementedError

    def use_latest_version(self):
        """
        Switch the working copy to the most recent version.
        
        Any uncommitted changes are retained/merged in.
        """
        raise NotImplementedError

    def status(self):
        """
        Return a dict containing the sets of files that have been modified,
        added, removed, are missing, not under version control ('unknown'),
        are being ignored, or are unchanged ('clean').
        """
        raise NotImplementedError

    def has_changed(self):
        """Are there any uncommitted changes to the working copy?"""
        raise NotImplementedError

    def diff(self):
        """Return the difference between working copy and repository."""
        raise NotImplementedError

    def get_username(self):
        """
        Return the username and e-mail of the current user, as understood by the
        version control system, in the format 'username <e-mail>'.
        """
        raise NotImplementedError
