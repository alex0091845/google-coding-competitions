echo "Setting up test files..."
mkdir -p test
cp -u ./secret/subtask1/1.in ./test/1.in
cp -u ./secret/subtask1/1.ans ./test/1.ans
cp -u ./secret/subtask2/1.in ./test/2.in
cp -u ./secret/subtask2/1.ans ./test/2.ans
echo "Done setting up!"

echo "Testing..."
python ./building_palidromes.py ./test/1.in ./test/1.out
diff ./test/1.out ./test/1.ans
python ./building_palidromes.py ./test/2.in ./test/2.out
diff ./test/2.out ./test/2.ans
echo "Testing finished!"