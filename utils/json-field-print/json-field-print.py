import json
import sys

if __name__ == '__main__':
    args = sys.argv
    if len(args) < 2:
        print('Usage: ' + args[0] + ' [json-field-name] [field-value]')
        exit(1)

    field = args[1]
    field_val = args[2]
    line_count = 1
    for line in sys.stdin:
        try:
            obj = json.loads(line)
            if field in obj:
                if obj[field]["string"] == field_val:
                    print(line)
        except Exception as e:
            print('Line ' + str(line_count) + ' Got exception from parsing JSON\n' + line )
            exit(1)
        line_count = line_count + 1
