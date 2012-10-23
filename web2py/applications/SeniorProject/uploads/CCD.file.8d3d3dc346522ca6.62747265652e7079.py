'''
  File: btree.shell   -- save as btree.py
  Author: Alysse Haferman
  Date: 10-22-12
  Description: This class contains the instance variables and methods of a B Tree
'''


from btreenode import BTreeNode
from stack import MyStack
from queue import Queue
from person import Person
from copy import deepcopy
import sys

class BTree:
    ''' This module implements the BTree class -- a tree of BTreeNodes. Items can
        be inserted and deleted from the tree. Each node must have at least
        degree items in it (except for the root node)
    '''
    def __init__(self, degree):
        # This method is complete.
        self.degree = degree
        self.rootNode = BTreeNode(degree)
        
        # If time, file creation code, etc.
        self.nodes = {}
        self.stackOfNodes = MyStack()
        self.rootNode.setIndex(1)
        self.writeAt(1, self.rootNode)
        self.rootIndex = 1
        self.freeIndex = 2

    def __str__(self):
        # This method is complete.
        st = '  The degree of the BTree is ' + str(self.degree)+\
             '.\n'
        st += '  The index of the root node is ' + \
              str(self.rootIndex) + '.\n'
        for x in range(1, self.freeIndex):
            node = self.readFrom(x)
            if node.getNumberOfKeys() > 0:
                st += str(node) 
        return st

    def delete(self, anItem):
        ''' Answer None if a matching item is not found.  If found,
          answer the entire item.  
        '''
        searchResult = self.searchTree(anItem)
        n = self.degree
        
        if searchResult['found']:                             #the item is in the tree; delete it
            aNode = self.readFrom(searchResult['fileIndex'])  #get the node that contains anItem
            nodeIndex = searchResult['nodeIndex']
            done = False
            
            if not aNode.isLeaf():                            #if anItem is in a leaf node, find the inorder successor
                (ioSuc, iosNode) = self.inorderSuccessor(aNode, nodeIndex)
                searchResult = self.searchTree(ioSuc)         #search the tree in order to get the stack of nodes on the search path                
                aNode.getItems()[nodeIndex] = ioSuc           #replace anItem with the inorder successor                                         
                iosNode.removeItem(0)                         #remove the inorder successor from its original node
                self.writeAt(aNode.getIndex(), aNode)         #write the revised aNode to the file
                aNode = iosNode                               #reset what aNode refers to 
                anItem = ioSuc
                
            else:                                             #if anItem was already in a leaf node
                aNode.removeItem(nodeIndex)                   #remove anItem from the leaf node
            
            while not done and aNode.getNumberOfKeys() < n and aNode.getIndex() != self.rootIndex: #while aNode has less than n keys and is not the root
                parentNode = self.stackOfNodes.pop()          #get the parent node
                (parentIndex, siblingNode, sibSide) = self.findParentAndSibling(anItem, parentNode) #get the parent index and the sibling
                totNumKeys = siblingNode.getNumberOfKeys() + aNode.getNumberOfKeys() + 1 #find the total number of keys, including the parent item
                
                tempNode = BTreeNode(2*n)                     #create a temporary BTreeNode
                                    
                if sibSide == "right":                        #if using the right sibling, copy aNode, then parent, then sibling
                    tempNode.copyItemsAndChildren(aNode, 0, aNode.getNumberOfKeys()-1, 0)
                    tempNode.getItems()[aNode.getNumberOfKeys()] = parentNode.getItems()[parentIndex]
                    tempNode.copyItemsAndChildren(siblingNode, 0, siblingNode.getNumberOfKeys()-1, aNode.getNumberOfKeys()+1)
                    
                else:                                         #if using the left sibling, copy the sibling, then parent, then aNode
                    tempNode.copyItemsAndChildren(siblingNode, 0, siblingNode.getNumberOfKeys()-1, 0)
                    tempNode.getItems()[siblingNode.getNumberOfKeys()] = parentNode.getItems()[parentIndex]
                    tempNode.copyItemsAndChildren(aNode, 0, aNode.getNumberOfKeys()-1, siblingNode.getNumberOfKeys()+1)
                    
                aNode.clear()                                 #clear the items and children from the two nodes
                siblingNode.clear()                
                
                if totNumKeys > 2*n:                          #case 2a: redistribute
                    sepKey = (totNumKeys + 1)//2              #find the new separating key     
                    
                    aNode.copyItemsAndChildren(tempNode, 0, sepKey-2, 0) #put the items of the temp node back to where they belong, redistributed
                    parentNode.getItems()[parentIndex] = tempNode.getItems()[sepKey-1] 
                    siblingNode.copyItemsAndChildren(tempNode, sepKey, totNumKeys-1, 0)
                    
                    aNode.setNumberOfKeys(sepKey-1)
                    siblingNode.setNumberOfKeys(totNumKeys-sepKey)
                
                else:                                         #case 2b: merge
                    parentNode.removeItem(parentIndex)        #remove the parent item from the parent node
                    
                    if sibSide == "right":                    #remove the child representing the right sibling
                        parentNode.removeChild(parentIndex+1)
                        if parentNode.getNumberOfKeys() == 0: #if the parent is now empty after the merge, make aNode the root of the tree
                            done = True
                            self.rootNode = aNode
                            self.rootIndex = aNode.getIndex()
                            
                        aNode.copyItemsAndChildren(tempNode, 0, totNumKeys-1, 0) #merge all the items into aNode
                        aNode.setNumberOfKeys(totNumKeys)                        
                            
                    else:                                     #remove the child representing the right sibling (aNode)
                        parentNode.removeChild(parentIndex+1)
                        if parentNode.getNumberOfKeys() == 0: #if the parent is now empty after the merge, make sibNode the root of the tree
                            done = True
                            self.rootNode = siblingNode
                            self.rootIndex = siblingNode.getIndex()
                            
                        siblingNode.copyItemsAndChildren(tempNode, 0, totNumKeys-1, 0) #merge all the items into the sibling node
                        siblingNode.setNumberOfKeys(totNumKeys)
                
                self.writeAt(aNode.getIndex(), aNode)         #write the updates to the file
                self.writeAt(siblingNode.getIndex(), siblingNode)
                self.writeAt(parentNode.getIndex(), parentNode)
                
                aNode = parentNode                            #move up the tree and check if it's ok
        
        else:                                                 #the item is not in the tree; return None
            return None

    def inorderSuccessor(self, node, nodeIndex):
        '''This method finds the inorder successor given the node containing 
           the original item and the node index of the original item. It 
           returns a tuple containing the inorder successor along with the 
           node containing the inorder successor
        '''
        fIndex = node.getChild()[nodeIndex+1]                #get the right child of the item
        aNode = self.readFrom(fIndex)                        #get the corresponding node
        
        while not aNode.isLeaf():                            #while it's not a leaf node
            fIndex = aNode.getChild()[0]                     #get the index of the left-most child
            aNode = self.readFrom(fIndex)                    #get the corresponding node
            
        inorderSuccessor = aNode.getItems()[0]               #get the inorder successor
        return (inorderSuccessor, aNode)
    
    def findParentAndSibling(self, anItem, parentNode):
        '''This method finds the parent index and the sibling node given the item and 
           the parent node.
           It returns the right child (if it exists), otherwise the left child.
        '''
        currentIndex = 0
        found = False
        parentItems = parentNode.getItems()
        parentChild = parentNode.getChild()
        
        while not found:                                       #find the index of the parent and the sibling
            if currentIndex == parentNode.getNumberOfKeys():   #we found the parent and we have a left sibling
                parentIndex = currentIndex - 1
                siblingIndex = parentChild[currentIndex-1]
                sibSide = "left"
                found = True            
            elif parentItems[currentIndex] > anItem:           #we found the parent and we have a right sibling
                parentIndex = currentIndex
                siblingIndex = parentChild[currentIndex+1]
                sibSide = "right"
                found = True              
            else:                                              #if haven't found parent yet, increment the currentIndex
                currentIndex += 1
            
        sibling = self.readFrom(siblingIndex)                  #get the sibling node
        
        return (parentIndex, sibling, sibSide)

    def inorderOn(self, aFile):
        '''
          Print the items of the BTree in inorder on the file 
          aFile.  aFile is open for writing.
          This method is complete at this time.
        '''
        aFile.write("An inorder traversal of the BTree:\n")
        self.inorderOnFrom( aFile, self.rootIndex)

    def inorderOnFrom(self, aFile, index):
        ''' Print the items of the subtree of the BTree, which is
          rooted at index, in inorder on aFile.
        '''
        node = self.readFrom(index)                    #get the node corresponding to the index
        for i in range(node.getNumberOfKeys()):        #for each item in the node
            left = node.getChild()[i]                  #get the index of the left child                       
            if left != None:                           #visit the left
                self.inorderOnFrom(aFile, left)
                
            aFile.write(str(node.getItems()[i])+"\n")  #visit the middle
            
        right = node.getChild()[node.getNumberOfKeys()]#get the index of the right child    
        if right != None:                              #visit the rightmost child
            self.inorderOnFrom(aFile, right)

    def insert(self, anItem):
        ''' Answer None if the BTree already contains a matching
          item. If not, insert a deep copy of anItem and answer
          anItem.
        '''
        searchResult = self.searchTree(anItem)                        #search for anItem
        if searchResult['found']:                                     #if anItem already exists in the tree, return None
            return None
        
        else:                                                         #if anItem doesn't exist in the tree
            insertNode = self.readFrom(searchResult['fileIndex'])     #get the node anItem should belong in
            if insertNode.isFull():                                   #if the node is full, need to split the node
                toParent = deepcopy(anItem)                           #make a deepcopy of the item we want to insert
                leftChild = None                                      #since inserting into a leaf node, left and right children are None
                rightChild = None
                
                while insertNode.isFull():
                    splitNode = insertNode.addItemAndSplit(toParent, leftChild, rightChild) #split the full node
                    splitNode.setIndex(self.freeIndex)                #set the index of the new node to be the next available index
                    self.freeIndex += 1                               #increment the free index number
                    
                    toParent = deepcopy(insertNode.getItems()[insertNode.getNumberOfKeys()-1]) #get the item that will go to the parent node
                    insertNode.getItems()[insertNode.getNumberOfKeys()-1] = None #get rid of the record of the parent item
                    insertNode.getChild()[insertNode.getNumberOfKeys()] = None   #get rid of the right child of the parent in the insertNode
                    insertNode.setNumberOfKeys(insertNode.getNumberOfKeys()-1)
                    
                    leftChild = insertNode.getIndex()                 #get the left and right indices of the parent
                    rightChild = splitNode.getIndex()
                    
                    self.writeAt(leftChild, insertNode)               #write both nodes to the file
                    self.writeAt(rightChild, splitNode)
                    
                    insertNode = self.stackOfNodes.pop()              #get the parent node
                    
                    if insertNode == None:                            #if there is no parent, create a new root node                                
                        insertNode = BTreeNode(self.degree)           #create a new node
                        insertNode.setIndex(self.freeIndex)           #set the index of the new root node
                        self.rootNode = insertNode                    
                        self.rootIndex = self.freeIndex               #set the root index
                        self.freeIndex += 1                           #increment the free index number
                    
                insertNode.insertItem(toParent, leftChild, rightChild)#if the parent node isn't full, just insert the item
                self.writeAt(insertNode.getIndex(), insertNode)       #write the final node to the file
                
            else:                                                     #there is room for anItem, so just perform an insert
                insertNode.insertItem(deepcopy(anItem))
                self.writeAt(searchResult['fileIndex'], insertNode)   #write the node to the file
            return anItem                                             #return the item
        
    def levelByLevel(self, aFile):
        ''' Print the nodes of the BTree level-by-level on aFile.
        '''
        aFile.write("A level-by-level listing of the nodes:\n")
        aQueue = Queue()                                              #create an empty queue
        aQueue.enqueue(self.rootNode)                                 #enqueue the root node
        
        while not aQueue.isEmpty():
            aNode = aQueue.dequeue()                                  #get the next node in the queue
            aFile.write(str(aNode))                                   #write the node to the file
            
            for i in range(aNode.getNumberOfKeys()+1):                #for each of the items in the node
                child = self.readFrom(aNode.getChild()[i])            #get the child node
                if child != None:                                     #if there is a child node, enqueue it
                    aQueue.enqueue(child)

    def readFrom(self, index):
        ''' Answer the node at entry index of the btree structure.
          Later adapt to files.  This method is complete at this time.
        '''
        if self.nodes.__contains__(index):
            return self.nodes[index]
        else:
            return None

    def recycle(self, aNode):
        # For now, do nothing
        # This method is complete at this time.
        aNode.clear()

    def retrieve(self, anItem):
        ''' If found, answer a deep copy of the matching item.
          If not found, answer None
        '''
        searchResult = self.searchTree(anItem)
        if searchResult['found']:                                       #if anItem is in the tree
            node = self.readFrom(searchResult['fileIndex'])             #get the node that anItem is in
            return deepcopy(node.getItems()[searchResult['nodeIndex']]) #return a deepcopy of anItem
        else:
            return None

    def searchTree(self, anItem):
        ''' Answer a dictionary.  If there is a matching item, at
          'found' is True, at 'fileIndex' is the index of the node
          in the BTree with the matching item, and at 'nodeIndex'
          is the index into the node of the matching item.  If not,
          at 'found' is False, but the entry for 'fileIndex' is the
          leaf node where the search terminated.  An important
          function of this method is that it pushes all of the
          nodes of the search path from the rootnode, down to,
          but not including the corresponding leaf node of a search
          (or the node containing a match).  Again, the rootnode
          is pushed if it is not a leaf node and has no match.
        '''
        self.stackOfNodes.clear()                          #clear the existing stack
        currentNode = self.readFrom(self.rootIndex)        #get the root node
        searchResult = currentNode.searchNode(anItem)      #search the root node for anItem
        
        while not searchResult['found'] and not currentNode.isLeaf(): #while we haven't found anItem and the current node we're looking at isn't a leaf node
            self.stackOfNodes.push(currentNode)            #push the current node onto the stack
            nextNodeIndex = currentNode.getChild()[searchResult['nodeIndex']] #get the next index on the search path
            currentNode = self.readFrom(nextNodeIndex)     #get the node associated with the next index
            searchResult = currentNode.searchNode(anItem)  #search that node for anItem
        
        searchResult['fileIndex'] = currentNode.getIndex() #set the file index to be the index of the last node searched
        return searchResult

    def update(self, anItem):
        ''' If found, update the item with a matching key to be a
          deep copy of anItem and answer anItem.  If not, answer None.
        '''
        searchResult = self.searchTree(anItem)                 #search for anItem
        if searchResult['found']:                              #if anItem is in the tree
            fileIndex = searchResult['fileIndex'] 
            nodeIndex = searchResult['nodeIndex']
            uNode = self.readFrom(fileIndex)                   #get the node that anItem is in
            if uNode != None:
                uNode.getItems()[nodeIndex] = deepcopy(anItem) #update the node with anItem
                return anItem
            else:
                return None
        else:
            return None

    def writeAt(self, index, aNode):
        ''' Set the element in the btree with the given index
          to aNode.  This method must be invoked to make any
          permanent changes to the btree.  We may later change
          this method to work with files.
          This method is complete at this time.
        '''
        self.nodes[index] = aNode


def main():
    print('My name is Alysse Haferman ')
    
    print( ' # run #1 -------------------------------' )
    bt = BTree(1)
    bt.insert(50)
    bt.insert(27)
    bt.insert(35)
    print( bt )
    
    bt.insert(98)
    bt.insert(201)
    print( bt )

    bt.insert(73)
    bt.insert(29)
    bt.insert(150)
    bt.insert(15)
    print( bt )

    bt.insert(64)
    print( bt )

    bt.insert(83)
    bt.insert(90)
    print( bt )

    bt.insert(87)
    bt.insert(253)
    print( bt )

    bt.insert(84)
    print( bt )
    
    
    print( ' # run #2 -------------------------------' )
    t = BTree(1)
    t.insert(Person('Joe', 38))
    t.insert(Person('Susie',48))
    t.insert(Person('Billy',39))
    t.insert(Person('Tomas',12))
    t.insert(Person('Don',35))
    t.update(Person('Willy', 12))
    print( t.retrieve(Person('', 48)) )
    print( t )

    t.levelByLevel(sys.stdout)
    t.inorderOn(sys.stdout)
    t.delete(Person("",35))
    t.inorderOn(sys.stdout)
    
    
    print( ' # run#3 -------------------------------' )
    bt = BTree(2)
    bt.insert(20)
    bt.insert(40)
    bt.insert(10)
    bt.insert(30)
    bt.insert(15)
    bt.insert(35)
    bt.insert(7)
    bt.insert(26)
    bt.insert(18)
    bt.insert(22)
    bt.insert(5)
    bt.insert(42)
    bt.insert(13)
    bt.insert(46)
    bt.insert(27)
    bt.insert(8)
    bt.insert(32)
    bt.insert(38)
    bt.insert(24)
    bt.insert(45)
    bt.insert(25)
    print( bt )
    
        
    print( ' # run#4 -------------------------------' )
    bt = BTree(2)
    bt.insert(20)
    bt.insert(40)
    bt.insert(10)
    bt.insert(30)
    bt.insert(15)
    bt.insert(35)
    bt.insert(7)
    bt.insert(26)
    bt.insert(18)
    bt.insert(22)
    bt.insert(5)
    bt.insert(42)
    bt.insert(13)
    bt.insert(46)
    bt.insert(27)
    bt.insert(8)
    bt.insert(32)
    bt.insert(38)
    bt.insert(24)
    bt.insert(45)
    bt.insert(25)
    bt.delete(35)
    bt.delete(38)
    bt.delete(25)
    bt.delete(38)
    print( bt )
    
    print( ' #run #5 -------------------------------' )
    bt = BTree(1)
    bt.insert(27)
    bt.insert(50)
    bt.insert(35)
    bt.insert(29)
    bt.insert(150)
    bt.insert(98)
    bt.insert(73)
    bt.insert(201)
    print( bt )
    bt.delete(35)
    bt.delete(98)
    bt.delete(29)
    bt.delete(73)
    bt.delete(50)
    bt.delete(150)
    bt.delete(12)
    bt.delete(98)
    print( bt )
    


if __name__ == '__main__': main()

''' The output:
 # run #1 -------------------------------
  The degree of the BTree is 1.
  The index of the root node is 3.
The contents of the node with index 1:
   Index   0  >  child: None   item: 27
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 35
                 child: 2

  The degree of the BTree is 1.
  The index of the root node is 3.
The contents of the node with index 1:
   Index   0  >  child: None   item: 27
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 35
   Index   1  >  child: 2   item: 98
                 child: 4
The contents of the node with index 4:
   Index   0  >  child: None   item: 201
                 child: None

  The degree of the BTree is 1.
  The index of the root node is 7.
The contents of the node with index 1:
   Index   0  >  child: None   item: 15
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
   Index   1  >  child: None   item: 73
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 27
                 child: 5
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
   Index   1  >  child: None   item: 201
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 29
                 child: None
The contents of the node with index 6:
   Index   0  >  child: 2   item: 98
                 child: 4
The contents of the node with index 7:
   Index   0  >  child: 3   item: 35
                 child: 6

  The degree of the BTree is 1.
  The index of the root node is 7.
The contents of the node with index 1:
   Index   0  >  child: None   item: 15
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 27
                 child: 5
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
   Index   1  >  child: None   item: 201
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 29
                 child: None
The contents of the node with index 6:
   Index   0  >  child: 2   item: 64
   Index   1  >  child: 8   item: 98
                 child: 4
The contents of the node with index 7:
   Index   0  >  child: 3   item: 35
                 child: 6
The contents of the node with index 8:
   Index   0  >  child: None   item: 73
                 child: None

  The degree of the BTree is 1.
  The index of the root node is 7.
The contents of the node with index 1:
   Index   0  >  child: None   item: 15
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 27
                 child: 5
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
   Index   1  >  child: None   item: 201
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 29
                 child: None
The contents of the node with index 6:
   Index   0  >  child: 2   item: 64
                 child: 8
The contents of the node with index 7:
   Index   0  >  child: 3   item: 35
   Index   1  >  child: 6   item: 83
                 child: 10
The contents of the node with index 8:
   Index   0  >  child: None   item: 73
                 child: None
The contents of the node with index 9:
   Index   0  >  child: None   item: 90
                 child: None
The contents of the node with index 10:
   Index   0  >  child: 9   item: 98
                 child: 4

  The degree of the BTree is 1.
  The index of the root node is 7.
The contents of the node with index 1:
   Index   0  >  child: None   item: 15
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 27
                 child: 5
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 29
                 child: None
The contents of the node with index 6:
   Index   0  >  child: 2   item: 64
                 child: 8
The contents of the node with index 7:
   Index   0  >  child: 3   item: 35
   Index   1  >  child: 6   item: 83
                 child: 10
The contents of the node with index 8:
   Index   0  >  child: None   item: 73
                 child: None
The contents of the node with index 9:
   Index   0  >  child: None   item: 87
   Index   1  >  child: None   item: 90
                 child: None
The contents of the node with index 10:
   Index   0  >  child: 9   item: 98
   Index   1  >  child: 4   item: 201
                 child: 11
The contents of the node with index 11:
   Index   0  >  child: None   item: 253
                 child: None

  The degree of the BTree is 1.
  The index of the root node is 15.
The contents of the node with index 1:
   Index   0  >  child: None   item: 15
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 27
                 child: 5
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 29
                 child: None
The contents of the node with index 6:
   Index   0  >  child: 2   item: 64
                 child: 8
The contents of the node with index 7:
   Index   0  >  child: 3   item: 35
                 child: 6
The contents of the node with index 8:
   Index   0  >  child: None   item: 73
                 child: None
The contents of the node with index 9:
   Index   0  >  child: None   item: 84
                 child: None
The contents of the node with index 10:
   Index   0  >  child: 9   item: 87
                 child: 12
The contents of the node with index 11:
   Index   0  >  child: None   item: 253
                 child: None
The contents of the node with index 12:
   Index   0  >  child: None   item: 90
                 child: None
The contents of the node with index 13:
   Index   0  >  child: 4   item: 201
                 child: 11
The contents of the node with index 14:
   Index   0  >  child: 10   item: 98
                 child: 13
The contents of the node with index 15:
   Index   0  >  child: 7   item: 83
                 child: 14

 # run #2 -------------------------------
Name: Susie Id: 48 
  The degree of the BTree is 1.
  The index of the root node is 3.
The contents of the node with index 1:
   Index   0  >  child: None   item: Name: Willy Id: 12 
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: Name: Susie Id: 48 
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: Name: Don Id: 35 
   Index   1  >  child: 4   item: Name: Billy Id: 39 
                 child: 2
The contents of the node with index 4:
   Index   0  >  child: None   item: Name: Joe Id: 38 
                 child: None

A level-by-level listing of the nodes: 
The contents of the node with index 3:
   Index   0  >  child: 1   item: Name: Don Id: 35 
   Index   1  >  child: 4   item: Name: Billy Id: 39 
                 child: 2
The contents of the node with index 1:
   Index   0  >  child: None   item: Name: Willy Id: 12 
                 child: None
The contents of the node with index 4:
   Index   0  >  child: None   item: Name: Joe Id: 38 
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: Name: Susie Id: 48 
                 child: None
An inorder traversal of the BTree:
Name: Willy Id: 12 
Name: Don Id: 35 
Name: Joe Id: 38 
Name: Billy Id: 39 
Name: Susie Id: 48 
An inorder traversal of the BTree:
Name: Willy Id: 12 
Name: Joe Id: 38 
Name: Billy Id: 39 
Name: Susie Id: 48 
 # run#3 -------------------------------
  The degree of the BTree is 2.
  The index of the root node is 9.
The contents of the node with index 1:
   Index   0  >  child: None   item: 5
   Index   1  >  child: None   item: 7
   Index   2  >  child: None   item: 8
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 22
   Index   1  >  child: None   item: 24
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 10
   Index   1  >  child: 5   item: 20
                 child: 2
The contents of the node with index 4:
   Index   0  >  child: None   item: 32
   Index   1  >  child: None   item: 35
   Index   2  >  child: None   item: 38
                 child: None
The contents of the node with index 5:
   Index   0  >  child: None   item: 13
   Index   1  >  child: None   item: 15
   Index   2  >  child: None   item: 18
                 child: None
The contents of the node with index 6:
   Index   0  >  child: None   item: 42
   Index   1  >  child: None   item: 45
   Index   2  >  child: None   item: 46
                 child: None
The contents of the node with index 7:
   Index   0  >  child: None   item: 26
   Index   1  >  child: None   item: 27
                 child: None
The contents of the node with index 8:
   Index   0  >  child: 7   item: 30
   Index   1  >  child: 4   item: 40
                 child: 6
The contents of the node with index 9:
   Index   0  >  child: 3   item: 25
                 child: 8

 # run#4 -------------------------------
  The degree of the BTree is 2.
  The index of the root node is 3.
The contents of the node with index 1:
   Index   0  >  child: None   item: 5
   Index   1  >  child: None   item: 7
   Index   2  >  child: None   item: 8
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 22
   Index   1  >  child: None   item: 24
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 10
   Index   1  >  child: 5   item: 20
   Index   2  >  child: 2   item: 26
   Index   3  >  child: 7   item: 42
                 child: 6
The contents of the node with index 5:
   Index   0  >  child: None   item: 13
   Index   1  >  child: None   item: 15
   Index   2  >  child: None   item: 18
                 child: None
The contents of the node with index 6:
   Index   0  >  child: None   item: 45
   Index   1  >  child: None   item: 46
                 child: None
The contents of the node with index 7:
   Index   0  >  child: None   item: 27
   Index   1  >  child: None   item: 30
   Index   2  >  child: None   item: 32
   Index   3  >  child: None   item: 40
                 child: None

 #run #5 -------------------------------
  The degree of the BTree is 1.
  The index of the root node is 3.
The contents of the node with index 1:
   Index   0  >  child: None   item: 27
   Index   1  >  child: None   item: 29
                 child: None
The contents of the node with index 2:
   Index   0  >  child: None   item: 50
   Index   1  >  child: None   item: 73
                 child: None
The contents of the node with index 3:
   Index   0  >  child: 1   item: 35
   Index   1  >  child: 2   item: 98
                 child: 4
The contents of the node with index 4:
   Index   0  >  child: None   item: 150
   Index   1  >  child: None   item: 201
                 child: None

  The degree of the BTree is 1.
  The index of the root node is 1.
The contents of the node with index 1:
   Index   0  >  child: None   item: 27
   Index   1  >  child: None   item: 201
                 child: None

'''
