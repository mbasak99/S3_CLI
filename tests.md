# Tests for A1 Cloud
## s3copy tests

### 1
`chlocn /s5-s3/folder_prime/another_folder/`
`s3copy last_folder/new_pic.png copy_folder_test/pic.png`

### 2
`chlocn /s5-s3/folder_prime`
`s3copy another_folder/last_folder/new_pic.png dab_for_haters/pic.png`

### 3
`s3copy /monark-test-cloud9/copy_pic.png /monark-test-cloud123123/pic.png`

## chlocn tests
### 1
`chlocn /s5-s3`
`chlocn folder_prime`

### 2
`chlocn /s5-s3`
`chlocn folder_prime`
`chlocn ..`
`chlocn folder_prime`
`chlocn another_folder`

## s3loccp tests
### 1
`s3loccp /s5-s3/pic.png test_folder/copy_test.png`

## list tests
### 1
`chlocn /s5-s3`
`list`

### 2
``
