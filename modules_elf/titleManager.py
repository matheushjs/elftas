#    ElfTAI specific CSV file manager.
#    Copyright (C) 2017 Matheus Henrique Junqueira Saldanha
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    Contact: matheus.saldanha@usp.br

import termcolor as tc
import csv

from .titleNode import TitleNode

# String stripping and trimming is done here.

class TitleManager:
    """Class that will manage a list of TitleNodes. Basically is supposed to do:
        1) Read a csv file, loading all Nodes in memory.
        2) Apply operations upon the list of Nodes.
        3) Saves the processed list of Nodes in a csv file.

    Exceptions:
        TypeError - When any argument received has invalid type.
                    Most arguments are expected to be strings.
                    Even list of strings are type-checked.
        ValueError - When a value given as argument is ignored for any reason,
                     forcing the function not to do what its name suggests.
                     Happens when trying to add an alias that already exists, for example.
        IndexError - When trying to access an element not in the list in question."""
    
    def __init__(self, filename, bkfile=None):
        # nodes: list of existent nodes
        # filename: name of file from which to read all nodes
        # bkfile: name of file to which backup all nodes
        self.nodes = []
        self.filename = filename
        self.bkfile = bkfile
        self.read_from_csv(filename)

    def close(self):
        """If this TitleManager was given a name for a backup file upon instantiation,
          transfer contents of the old Nodes csv file to this backup.
        Then saves all nodes in the Nodes csv file, overwriting it."""
        if self.bkfile:
            self.write_to_csv(self.filename, self.bkfile)
        else:
            self.write_to_csv(self.filename)

    def print_summary(self):
        """Prints all nodes, each one occupying a single line.
        Information diplayed is only the Node's title and aliases."""
        for node in self.nodes:
            node.print_line(40)

    def print_full(self, string=None, length=-1):
        """Prints all information about nodes.
        If 'string' is given, prints full information about only the node identified by it.
        If 'string is NOT given, prints information for all nodes.
        If 'length' is given, prints only the latest 'length' items added to the Title.
        Raises:
            ValueError - 'string' is given, but the node cannot be found."""
        if string is not None:
            node = self._find_node_byName(string)
            if not node:
                raise ValueError
            node.print_block(length)
        else:
            for node in self.nodes:
                node.print_block(length)

    def add_node(self, title):
        """Adds a node to the list of Nodes.
        Node will have title 'title'. Make sure to get the case of this string correctly.
        Raises:
            ValueError - Node with same title already existed, so new node wasn't added."""
        node = self._find_node_byName(title)
        if node is not None:
            raise ValueError
        
        node = TitleNode(title)
        self.nodes.append(node)
        self.nodes.sort()

    def rm_node(self, string):
        """Removes the node identified by 'string' from the list of Nodes.
        String comparison is made case-insensitively here.
        Raise:
            ValueError - node didn't exist anyway."""
        node = self._find_node_byName(string)
        self.nodes.remove(node)

    def add_alias(self, string, alias):
        """Adds alias to node identified by 'string'.
        Node searching is made case-insensitively.
        Raise:
            ValueError - Node wasn't found. Or some node already has the given alias.
                         Exception raised with due explanation message."""
        if self._find_node_byName(alias):
            raise ValueError("Node with given alias already exists.")

        node = self._find_node_byName(string)
        if not node:
            raise ValueError("Could not identify node.")
        node.add_alias(alias)

    def rm_alias(self, alias):
        """Removes alias from the list of nodes.
        Raise:
            ValueError - Node with given alias has not been found."""
        if isinstance(alias, str):
            node = self._find_node_byName(alias)
            if not node:
                raise ValueError
            node.rm_alias(alias)
        else:
            raise TypeError

    def set_comment(self, string, n, comm):
        """Replaces the n-th comment of node identified by 'string'.
        returns:
            The comment string that has been replaced
        Raise:
            ValueError if node could not be identified
            IndexError if comment of given index does not exist"""
        node = self._find_node_byName(string)
        if not node:
            raise ValueError
        
        comment = node.get_comment()
        temp = comment[n]
        comment[n] = comm
        return temp

    def add_comment(self, string, comm):
        """Adds a comment to node identified by 'string'.
        Returns False if node doesn't exist.
        Raise:
            ValueError if node could not be identified
            IndexError if comment of given index does not exist"""
        node = self._find_node_byName(string)
        if not node:
            raise ValueError
        comment = node.get_comment()
        comment.add(comm)

    def rm_comment(self, string, idx):
        """Removes the idx-th comment of the node identified by 'string'
        Returns the removed comment.
        Raises:
            ValueError if node could not be identified
            IndexError if comment of given index does not exist"""
        node = self._find_node_byName(string)
        if not node:
            raise ValueError
        return node.get_comment().rm(idx)

    def add_item(self, string, item):
        """Adds a unique item 'item' to the node identified by 'string'.
        Note that items are unique to a single node, but can appear in more than 1 node at a time.
        Raise:
            ValueError - Node couldn't be found or the item already existed in the node found.
                         Raised with due explanation message."""
        node = self._find_node_byName(string)
        if not node:
            raise ValueError("Node could not be identified")
        try:
            node.add_item(item)
        except ValueError:
            raise ValueError("Item already exists in the node.")

    def rm_item(self, string, item):
        """Removes the item 'item' from the node identified by 'string'.
        Raise:
            ValueError - Node could not be found, or the identified node didn't have that item.
                         Raised with due explanation message"""
        node = self._find_node_byName(string)
        if not node:
            raise ValueError("Node could not be identified")
        try:
            node.rm_item(item)
        except ValueError:
            raise ValueError("Node does not have given item.")

    def find_item(self, item):
        """Returns all Nodes that contain item 'item'.
        Return:
            List with all TitleNode containing the given item."""
        lnodes = []
        for node in self.nodes:
            if node.has_item(item) >= 0:
                lnodes.append(node)
        
        return lnodes

    def read_from_csv(self, path):
        """Reads all TitleNodes on a csv file, and store them internally."""
        if not isinstance(path, str):
            raise TypeError

        try:
            with open(path) as fp:
                rd = csv.reader(fp)
                while True:
                    try:
                        node = TitleNode().read_from_csv(rd)
                    except ValueError: break
                    self.nodes.append(node)
        except FileNotFoundError:
            open(path, "w") # May throw another FileNotFoundError, depending on 'path'

    def write_to_csv(self, path, bkpath=None):
        """Writes all TitleNodes to the csv file.
        If 'bkpath' is given, backup the main file before overwriting it."""
        if not isinstance(path, str):
            raise TypeError

        # Overwrite original file. Nothing should go wrong, so extra caution is taken.
        try:
            with open(path, 'r') as fp:
                safebuf = fp.read()
        except:
            safebuf = None

        try:
            with open(path, 'w') as fp:
                wr = csv.writer(fp)
                for node in self.nodes:
                    node.write_to_csv(wr)
        except:
            print("FATAL: Exception upon overwriting original CSV file. Attempting to undo overwriting.")
            if safebuf:
                with open(path, 'w') as fp:
                    fp.write(savebuf)

        # Saves the backup
        if bkpath and safebuf:
            with open(bkpath, 'w') as outfile:
                outfile.write(safebuf)

    def _find_node_byName(self, string):
        """Given a string, attemps to find the node with alias or title
        that is equivalent to the string.
        Comparison is done case-insensitive and ignoring blank characters.
        Returns None if no node was found"""
        string = string.strip().lower()
        for node in self.nodes:
            l = []
            l.append(node.get_title().strip().lower())
            l.extend([i for i in node.get_alias()]) 
            if string in l:
                return node
        return None
