# A Simple Class for Chaining References to Complex Objects

## The problem:
Python allows the standard, list, tuple, and dictionary primitive types,
and provides accessors that are either name- or index based.

So, given something like:
```python
d = {'a': 18, 'b': {'c': 7}, 'f': [2, 6, 9, 11], 'g': (8, 7, 6, 5)}
```
we would like to be able write something simple like
```python
value = d['b','c']
```
to get the value of '7'.
If you **know** the structure will be cooperative, then you can write:
```python
value = d['b']['c']
```
and so there would be little benefit.
However, if you want to have the behavior where the indexing is safe,
and returning **None** rather than throwing an exception, then
you can use the following code fragment.
Note, this was inspired by Scala's elegant way of dealing with optional
types, and the way they mesh nicely with lists of zero or one size.

If there is an easier way, please drop me a note!

```python
class WrappedComplexObject:

    def __init__(self, the_dict):
        self.dict = the_dict

    @staticmethod
    def is_addressable_type(x):
      return isinstance(x, list) or \
             isinstance(x, tuple)

    def __getitem__(self, indices):
        if not isinstance(indices, tuple):
            indices = tuple(indices)
        current = self.dict
        for idx in indices:
            if current and isinstance(current, dict):
                current = current.get(idx, None)
            elif current and WrappedComplexObject.is_addressable_type(current) and \
                 isinstance(idx, int):
                current = current[idx] if idx < len(current) else None
            else:
                current = None
        return current
```
Example usages include:
```python
d = {'a': 18, 'b': {'c': 7}, 'f': [2, 6, 9, 11], 'g': (8, 7, 6, 5)}
w = WrappedComplexObject(d)
z = w['a']
z = w['b', 'c']
z = w['a', 'c']
z = w['f', 1]
z = w['g', 1]
```
