class BinarySearch:
    def __init__(self, arr):
        self.arr = sorted(arr)  # Ensure the array is sorted

    def search(self, target):
        left, right = 0, len(self.arr) - 1
        while left <= right:
            mid = (left + right) // 2
            if self.arr[mid] == target:
                return mid
            elif self.arr[mid] < target:
                left = mid + 1
            else:
                right = mid - 1
        return -1  # Not found

# Usage
arr = [34, 7, 23, 32, 5, 62]
target = 23

bs = BinarySearch(arr)
index = bs.search(target)

if index != -1:
    print(f"Element {target} found at index {index}")
else:
    print(f"Element {target} not found")
