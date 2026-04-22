from datasets import load_dataset
ds = load_dataset('ComplexDataLab/OpenFake', split='train', streaming=True)
item = next(iter(ds))
print(f"Label is {type(item['label'])}: {item['label']}")
