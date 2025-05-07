import pdfplumber
import re

# Path to the academic transcript PDF
PDF_PATH = "historico.pdf"

# 1) this will split on every line that *begins* with a code (but keep the code
#    on the entry thanks to the lookahead)
ENTRY_SPLIT_RE = re.compile(
    r'(?m)(?=^[A-Z]{2,3}\d{3,4}\s+)', 
)

# 2) flatten out all whitespace in the entry
WHITESPACE_RE = re.compile(r'\s+')

# 3) now a single regex to grab everything in one go:
ENTRY_RE = re.compile(
    r'^'
    r'([A-Z]{2,3}\d{3,4})'       # 1) course code
    r'\s+(.+?)'                  # 2) course name (non-greedy)
    r'\s+(\d{2,3})'              # 3) credit hours
    r'\s+(-|\d{1,3})'            # 4) grade or "-"
    r'\s+(\d+%|-)'               # 5) frequency or "-"
    r'\s+(Aprovado|Cancelado|Matriculado)'  # 6) status
    r'.*$',                      # anything else after (e.g. “Observação”)
    re.UNICODE
)

def extract_courses_and_grades(pdf_path):
    results = []

    # 1) Read the whole PDF into one big string
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(
            page.extract_text() or "" for page in pdf.pages
        )

    # 2) Split into entries (first chunk may be header—skip it)
    chunks = ENTRY_SPLIT_RE.split(full_text)
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        # 3) Collapse all whitespace to single spaces
        flat = WHITESPACE_RE.sub(" ", chunk)

        # 4) Try to match our big entry regex
        m = ENTRY_RE.match(flat)
        if not m:
            continue

        code, name, ch, grade, freq, status = m.groups()

        # If it was cancelled, force grade to "-"
        if status == "Cancelado":
            grade = "-"

        results.append((code, name, ch, grade, status, freq))

    return results

def main():
    try:
        courses = extract_courses_and_grades(PDF_PATH)
        
        if not courses:
            print("No courses found in the PDF. Please check the file and pattern.")
            return
            
        print("Courses and Grades:")
        print("{:<10} {:<50} {:<5} {:<6} {:<15} {:<10}".format(
            "CODE", "COURSE NAME", "CH", "GRADE", "STATUS", "FREQUENCY"))
        print("-" * 100)
        
        total_credits = 0
        completed_credits = 0
        weighted_sum = 0
        
        for code, name, credit_hours, grade, status, frequency in courses:
            # Truncate long course names for display
            display_name = name[:47] + "..." if len(name) > 47 else name
            print("{:<10} {:<50} {:<5} {:<6} {:<15} {:<10}".format(
                code, display_name, credit_hours, grade, status, frequency))
                
            # Update statistics
            try:
                ch = int(credit_hours)
                total_credits += ch
                
                if status == 'Aprovado' and grade != '-':
                    completed_credits += ch
                    weighted_sum += int(grade) * ch
            except ValueError:
                # Skip if credit hours or grade can't be converted to int
                print(f"Warning: Could not process statistics for {code}")
        
        # Calculate and display statistics
        print("\nStatistics:")
        print(f"Total credit hours: {total_credits}")
        print(f"Completed credit hours: {completed_credits}")
        
        if completed_credits > 0:
            gpa = weighted_sum / completed_credits
            print(f"GPA (0-100 scale): {gpa:.2f}")
            print(f"GPA (0-4 scale: {(gpa/100*4):.2f}")
            
            # Show progress towards degree completion
            if total_credits > 0:
                completion_percentage = (completed_credits / 3200) * 100  # 3200 is the total required for graduation
                print(f"Progress towards graduation: {completion_percentage:.1f}% ({completed_credits}/3200 credits)")
    
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()