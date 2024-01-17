import xml.etree.ElementTree as ET
import os 

class XMLProcessor:
    def __init__(self, whitelistedFile, blacklistedFile):
        self.whitelistedFile = whitelistedFile
        self.blacklistedFile = blacklistedFile
        self.output_file_paths = [self.generate_output_path(self.whitelistedFile), self.generate_output_path(self.blacklistedFile)]

    def generate_output_path(self, input_path):
        base_name = os.path.basename(input_path)
        name, ext = os.path.splitext(base_name)
        output_file_name = f"output_{name}.txt"
        return os.path.join('./files', output_file_name)

    
    def extract_classes(self, element, classes_list):
        if element.tag == 'Item':
            class_name = element.get('class')
            if class_name:
                classes_list.append(class_name)

        for child in element:
            self.extract_classes(child, classes_list)

    def traverse_items(self, element, output_file):
        if element.tag == 'Item':
            class_info = f"Class: {element.get('class')}, Referent: {element.get('referent')}"
            script_guid = element.find(".//string[@name='ScriptGuid']")
            if script_guid is not None:
                script_guid_text = script_guid.text.strip() if script_guid.text else ''
                class_info += f", ScriptGuid: {script_guid_text}"
            output_file.write(f"{class_info}\n")

        for child in element:
            self.traverse_items(child, output_file)

    def process_rbxmx(self, input_path, output_path):
        with open(input_path, 'rb') as file:
            try:
                content = file.read().decode('utf-8', errors='replace')
                root = ET.fromstring(content)
            except ET.ParseError as e:
                print(f"Error parsing XML file: {e}")
                return

        with open(output_path, 'w') as output_file:
            self.traverse_items(root, output_file)
    def extract_classes_from_file(self, file_path):
        classes = []
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                self.extract_classes(ET.fromstring(content), classes)
        except ET.ParseError as e:
            return
        return classes

    def compare_class_orders(self, file_path1, file_path2):
        classes1, classes2 = self.extract_classes_from_file(file_path1), self.extract_classes_from_file(file_path2)
        return classes1 == classes2

    def apply_references_and_script_guids(self, input_path, reference_file_path, output_path):
        try:
            tree = ET.parse(input_path)
            root = tree.getroot()

            with open(reference_file_path, 'r') as reference_file:
                lines = reference_file.readlines()

            for line, element in zip(lines, self.traverse_items2(root)):
                if line.startswith("Class:"):
                    class_name, referent, script_guid = self.extract_info_from_line(line)
                    element.set('referent', referent)

                    script_guid_element = element.find(".//string[@name='ScriptGuid']")
                    if script_guid_element is not None:
                        script_guid_element.text = script_guid
                    else:
                        ET.SubElement(element, 'string', attrib={'name': 'ScriptGuid'}).text = script_guid

            tree.write(output_path)
            print(f"Successfully applied referents and ScriptGuids to {output_path}")

        except ET.ParseError as e:
            return
        except Exception as e:
            print(f"An error occurred: {e}")

    def extract_info_from_line(self, line):
        parts = line.split(',')
        class_name = parts[0].split(': ')[1].strip()
        referent = parts[1].split(': ')[1].strip()
        script_guid = parts[2].split(': ')[1].strip() if len(parts) > 2 else ''
        return class_name, referent, script_guid

    def traverse_items2(self, element):
        items = []
        if element.tag == 'Item':
            items.append(element)
        for child in element:
            items.extend(self.traverse_items2(child))
        return items

    def run(self):
        for input_path, output_path in zip([self.whitelistedFile, self.blacklistedFile], self.output_file_paths):
            self.process_rbxmx(input_path, output_path)
        result = self.compare_class_orders(self.output_file_paths[0], self.output_file_paths[1])

        if result:
            print("The order of classes is the same in both output files.")
            input_path = self.blacklistedFile
            reference_file_path = './files/output_rebuilt.txt'
            output_path = 'unblacklisted.rbxmx'

            self.apply_references_and_script_guids(input_path, reference_file_path, output_path)
        else:
            print("The order of classes is different in the two output files.")

if __name__ == "__main__":
    blacklistedFile = './files/Blacklisted.rbxmx'
    whitelistedFile = './files/rebuilt.rbxmx'

    processor = XMLProcessor(whitelistedFile, blacklistedFile)
    processor.run()

