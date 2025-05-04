def merge_sort(arr):
    if len(arr) <= 1:
        return arr

    # Divide
    mid = len(arr) // 2
    left_half = merge_sort(arr[:mid])
    right_half = merge_sort(arr[mid:])

    # Conquer (merge)
    return merge(left_half, right_half)


def merge(left, right):
    result = []
    i = j = 0

    # Merge while comparing elements
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

    # Add remaining elements from both halves
    result.extend(left[i:])
    result.extend(right[j:])
    return result


# Example usage
if __name__ == "__main__":
    arr = [5, 2, 9, 1, 5, 6]
    print("Original:", arr)
    sorted_arr = merge_sort(arr)
    print("Sorted:  ", sorted_arr)
