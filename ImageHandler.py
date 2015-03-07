from PIL import Image
from GPSFromExif import get_exif_data
import time

def merge(arr1, arr2):
	result = []
	arr1_index = 0
	arr2_index = 0
	while arr1_index < len(arr1) or arr2_index < len(arr2):
		if arr1_index == len(arr1):
			result.append(arr2[arr2_index])
			arr2_index += 1
		elif arr2_index == len(arr2):
			result.append(arr1[arr1_index])
			arr1_index += 1
		else:
			arr1_exif = get_exif_data(Image.open(arr1[arr1_index]))
			arr2_exif = get_exif_data(Image.open(arr2[arr2_index]))
			if time.strptime(str(arr1_exif['DateTime']), '%Y:%m:%d %H:%M:%S') < time.strptime(str(arr2_exif['DateTime']), '%Y:%m:%d %H:%M:%S'):
				result.append(arr1[arr1_index])
				arr1_index += 1
			else:
				result.append(arr2[arr2_index])
				arr2_index += 1
	return result

def split(a_list):
    half = len(a_list)/2
    return a_list[:half], a_list[half:]

def mergeSortHelper(arr, length):
	if length == 1:
		return arr
	left, right = split(arr)
	left = mergeSortHelper(left, length/2)
	right = mergeSortHelper(right, length/2)

	result = merge(left, right)
	return result

def mergeSort(arr):
	return mergeSortHelper(arr, len(arr))

'''if __name__ == "__main__":
	test = ['./test images/test1.jpg','./test images/test2.jpg', './test images/test3.jpg', './test images/test4.jpg', \
		'./test images/test5.jpg', './test images/test6.jpg', './test images/test7.jpg', './test images/test8.jpg']
	final = mergeSort(test)
	for location in final:
		image = Image.open(location)
		print str(get_exif_data(image)['DateTime'])'''