#
# Copyright (C) 2020  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 31 Milk Street #960789 Boston, MA
# 02196 USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
import dnf.callback
import dnf.transaction

from pyanaconda.anaconda_loggers import get_module_logger
from pyanaconda.core.i18n import _
from pyanaconda.modules.common.errors.installation import PayloadInstallationError

log = get_module_logger(__name__)

__all__ = ["TransactionProgress", "process_transaction_progress"]


def process_transaction_progress(queue, callback):
    """Process the transaction progress.

    When the installation works correctly it will end by 'quit' token.

    :param queue: a process shared queue
    :param callback: a callback for progress reporting
    :raise PayloadInstallationError: if the transaction fails
    """
    (token, msg) = queue.get()

    while token:
        if token == 'install':
            callback(_("Installing {}").format(msg))
        elif token == 'configure':
            callback(_("Configuring {}").format(msg))
        elif token == 'log':
            log.info(msg)
        elif token == 'post':
            callback(_("Performing post-installation setup tasks"))
        elif token == 'quit':
            log.info(msg)
            break  # Installation finished successfully
        elif token == 'error':
            log.error(msg)
            raise PayloadInstallationError("An error occurred during the transaction: " + msg)

        (token, msg) = queue.get()


class TransactionProgress(dnf.callback.TransactionProgress):
    """The class for receiving information about an ongoing transaction."""

    def __init__(self, queue):
        """Create a new instance.

        :param queue: a process shared queue
        """
        super().__init__()
        self._queue = queue
        self._last_ts = None
        self._postinst_phase = False
        self.cnt = 0

    def progress(self, package, action, ti_done, _ti_total, ts_done, ts_total):
        """Report ongoing progress on the given transaction item.

        :param package: the DNF package object
        :param action: the ID of the current action
        :param ti_done: the number of processed bytes of the transaction item
        :param _ti_total: the total number of bytes of the transaction item
        :param ts_done: the number of actions processed in the whole transaction
        :param ts_total: the total number of actions in the whole transaction
        """
        # Process DNF actions, communicating with anaconda via the queue
        # A normal installation consists of 'install' messages followed by
        # the 'post' message.
        if action == dnf.transaction.PKG_INSTALL and ti_done == 0:
            # do not report same package twice
            if self._last_ts == ts_done:
                return
            self._last_ts = ts_done

            msg = '%s.%s (%d/%d)' % \
                (package.name, package.arch, ts_done, ts_total)
            self.cnt += 1
            self._queue.put(('install', msg))

            # Log the exact package nevra, build time and checksum
            nevra = "%s-%s.%s" % (package.name, package.evr, package.arch)
            log_msg = "Installed: %s %s %s" % (nevra, package.buildtime, package.returnIdSum()[1])
            self._queue.put(('log', log_msg))

        elif action == dnf.transaction.TRANS_POST:
            self._queue.put(('post', None))
            log_msg = "Post installation setup phase started."
            self._queue.put(('log', log_msg))
            self._postinst_phase = True

        elif action == dnf.transaction.PKG_SCRIPTLET:
            # Log the exact package nevra, build time and checksum
            nevra = "%s-%s.%s" % (package.name, package.evr, package.arch)
            log_msg = "Configuring (running scriptlet for): %s %s %s" % (nevra, package.buildtime,
                                                                         package.returnIdSum()[1])
            self._queue.put(('log', log_msg))

            # only show progress in UI for post-installation scriptlets
            if self._postinst_phase:
                msg = '%s.%s' % (package.name, package.arch)
                self._queue.put(('configure', msg))

    def error(self, message):
        """Report an error that occurred during the transaction.

        :param message: a string that describes the error
        """
        self._queue.put(('error', message))

    def quit(self, message):
        """Report the end of the transaction and close the queue.

        :param message: the reason why the transaction ended
        """
        self._queue.put(('quit', message))
        self._queue.close()
