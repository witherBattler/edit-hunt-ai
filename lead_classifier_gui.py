import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os

class LeadClassifierGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Lead Classifier - Manual Review [1=Job, 0=NotJob, Del=Delete, ←→=Navigate]")
        self.root.geometry("1000x700")
        
        # Data storage
        self.leads = []
        self.current_index = 0
        self.true_leads = []  # Confirmed job opportunities (label=1)
        self.false_leads = []  # Not job opportunities (label=0)
        self.deleted_leads = set()  # Track deleted/removed leads (by index)
        self.reviewed_indices = set()  # Track which leads have been reviewed
        
        # Auto-save functionality
        self.auto_save_timer = None
        self.auto_save_delay = 10000  # 10 seconds in milliseconds
        self.last_save_status = ""
        
        # Load data
        self.load_leads()
        
        # Try to load previous session automatically
        self.load_session_silently()
        
        # Setup GUI
        self.setup_gui()
        
        # Display first lead
        if self.leads:
            self.display_current_lead()
    
    def load_leads(self):
        """Load leads from leads.jsonl file"""
        try:
            with open('leads.jsonl', 'r', encoding='utf-8') as f:
                for line in f:
                    lead = json.loads(line.strip())
                    self.leads.append(lead)
            print(f"Loaded {len(self.leads)} leads")
        except FileNotFoundError:
            messagebox.showerror("Error", "leads.jsonl file not found!")
            self.root.quit()
        except Exception as e:
            messagebox.showerror("Error", f"Error loading leads: {str(e)}")
            self.root.quit()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Progress info
        self.progress_label = ttk.Label(main_frame, text="", font=("Arial", 12, "bold"))
        self.progress_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Navigation frame
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, columnspan=3, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Button(nav_frame, text="← Previous", command=self.previous_lead).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="Next →", command=self.next_lead).pack(side=tk.LEFT, padx=(0, 20))
        
        # Jump to specific lead
        ttk.Label(nav_frame, text="Go to lead:").pack(side=tk.LEFT, padx=(0, 5))
        self.jump_entry = ttk.Entry(nav_frame, width=10)
        self.jump_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(nav_frame, text="Go", command=self.jump_to_lead).pack(side=tk.LEFT)
        
        # Lead content display
        content_frame = ttk.LabelFrame(main_frame, text="Lead Content", padding="10")
        content_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        self.content_text = scrolledtext.ScrolledText(
            content_frame, 
            wrap=tk.WORD, 
            font=("Arial", 11),
            height=15
        )
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text highlighting tags
        self.content_text.tag_config("green_highlight", background="#90EE90", foreground="black")  # Light green
        self.content_text.tag_config("red_highlight", background="#FFB6C1", foreground="black")    # Light red
        
        # Classification buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=(0, 10))
        
        # Large classification buttons
        self.true_button = ttk.Button(
            button_frame, 
            text="✓ REAL JOB OPPORTUNITY (Keep as Label=1)", 
            command=self.classify_as_true
        )
        self.true_button.pack(side=tk.LEFT, padx=(0, 10), ipadx=15, ipady=10)
        
        self.false_button = ttk.Button(
            button_frame, 
            text="✗ NOT A JOB OPPORTUNITY (Label=0)", 
            command=self.classify_as_false
        )
        self.false_button.pack(side=tk.LEFT, padx=(10, 10), ipadx=15, ipady=10)
        
        self.delete_button = ttk.Button(
            button_frame, 
            text="🗑️ DELETE (Remove duplicate/unwanted)", 
            command=self.delete_lead
        )
        self.delete_button.pack(side=tk.LEFT, padx=(10, 0), ipadx=15, ipady=10)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="10")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.stats_label = ttk.Label(stats_frame, text="", font=("Arial", 10))
        self.stats_label.grid(row=0, column=0)
        
        # Save and exit buttons
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3)
        
        ttk.Button(action_frame, text="Save Progress", command=self.manual_save_progress).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Save & Exit", command=self.save_and_exit).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(action_frame, text="Load Previous Session", command=self.load_previous_session).pack(side=tk.LEFT)
        
        # Auto-save status
        self.auto_save_label = ttk.Label(action_frame, text="", font=("Arial", 9), foreground="gray")
        self.auto_save_label.pack(side=tk.LEFT, padx=(20, 0))
        
        # Keyboard bindings
        self.root.bind('<Key-1>', lambda e: self.classify_as_true())
        self.root.bind('<Key-0>', lambda e: self.classify_as_false())
        self.root.bind('<Delete>', lambda e: self.delete_lead())
        self.root.bind('<Left>', lambda e: self.previous_lead())
        self.root.bind('<Right>', lambda e: self.next_lead())
        self.root.focus_set()  # Enable keyboard events
        
        # Start auto-save timer
        self.reset_auto_save_timer()
    
    def display_current_lead(self):
        """Display the current lead"""
        if not self.leads or self.current_index >= len(self.leads):
            return
        
        lead = self.leads[self.current_index]
        
        # Mark lead as reviewed just by viewing it (unless it's deleted)
        was_new = self.current_index not in self.reviewed_indices
        if self.current_index not in self.deleted_leads:
            self.reviewed_indices.add(self.current_index)
        
        # Update progress
        reviewed_count = len(self.reviewed_indices)
        deleted_count = len(self.deleted_leads)
        remaining_count = len(self.leads) - reviewed_count - deleted_count
        
        # Show if current lead is deleted
        status = "DELETED" if self.current_index in self.deleted_leads else "REVIEWED"
        
        self.progress_label.config(
            text=f"Lead {self.current_index + 1} of {len(self.leads)} | "
                 f"Reviewed: {reviewed_count} | Deleted: {deleted_count} | "
                 f"Remaining: {remaining_count}"
        )
        
        # Display content
        self.content_text.delete(1.0, tk.END)
        self.content_text.insert(1.0, lead['text'])
        
        # Apply text highlighting
        self.highlight_keywords()
        
        # Color coding: red for deleted, blue for reviewed
        if self.current_index in self.deleted_leads:
            self.content_text.config(bg="#ffe6e6")  # Light red background for deleted
        else:
            self.content_text.config(bg="#f0f8ff")  # Light blue background for reviewed
        
        # Update stats
        self.update_stats()
        
        # Update button states
        self.root.title(f"Lead Classifier - Lead {self.current_index + 1}/{len(self.leads)} - {status}")
        
        # Reset auto-save timer if this is a new view
        if was_new:
            self.reset_auto_save_timer()
    
    def highlight_keywords(self):
        """Highlight specific keywords in the text"""
        # Define keywords to highlight
        green_keywords = ["video editor", "hiring"]
        red_keywords = ["for hire"]
        
        # Get all text content
        text_content = self.content_text.get(1.0, tk.END).lower()
        
        # Clear existing highlighting tags
        self.content_text.tag_remove("green_highlight", 1.0, tk.END)
        self.content_text.tag_remove("red_highlight", 1.0, tk.END)
        
        # Highlight green keywords
        for keyword in green_keywords:
            start_pos = 1.0
            while True:
                pos = self.content_text.search(keyword, start_pos, tk.END, nocase=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(keyword)}c"
                self.content_text.tag_add("green_highlight", pos, end_pos)
                start_pos = end_pos
        
        # Highlight red keywords
        for keyword in red_keywords:
            start_pos = 1.0
            while True:
                pos = self.content_text.search(keyword, start_pos, tk.END, nocase=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(keyword)}c"
                self.content_text.tag_add("red_highlight", pos, end_pos)
                start_pos = end_pos
    
    def update_stats(self):
        """Update statistics display"""
        true_count = len(self.true_leads)
        false_count = len(self.false_leads)
        deleted_count = len(self.deleted_leads)
        total_reviewed = len(self.reviewed_indices)
        
        stats_text = (
            f"Job Opportunities: {true_count} | "
            f"Non-Jobs: {false_count} | "
            f"Deleted: {deleted_count} | "
            f"Reviewed: {total_reviewed}"
        )
        self.stats_label.config(text=stats_text)
    
    def classify_as_true(self):
        """Classify current lead as a real job opportunity"""
        if self.current_index < len(self.leads):
            lead = self.leads[self.current_index].copy()
            lead['label'] = 1
            
            # Remove from false_leads if it was there
            self.false_leads = [l for l in self.false_leads if l['text'] != lead['text']]
            
            # Add to true_leads if not already there
            if not any(l['text'] == lead['text'] for l in self.true_leads):
                self.true_leads.append(lead)
            
            self.reviewed_indices.add(self.current_index)
            self.reset_auto_save_timer()
            self.next_lead()
    
    def classify_as_false(self):
        """Classify current lead as not a job opportunity"""
        if self.current_index < len(self.leads):
            lead = self.leads[self.current_index].copy()
            lead['label'] = 0
            
            # Remove from true_leads if it was there
            self.true_leads = [l for l in self.true_leads if l['text'] != lead['text']]
            
            # Add to false_leads if not already there
            if not any(l['text'] == lead['text'] for l in self.false_leads):
                self.false_leads.append(lead)
            
            self.reviewed_indices.add(self.current_index)
            self.reset_auto_save_timer()
            self.next_lead()
    
    def delete_lead(self):
        """Delete/remove current lead (will not be saved to either file)"""
        if not self.leads or self.current_index >= len(self.leads):
            return
        
        # Mark as deleted
        self.deleted_leads.add(self.current_index)
        
        # Remove from reviewed status since it's deleted
        self.reviewed_indices.discard(self.current_index)
        
        # Remove from both true_leads and false_leads if it exists there
        current_text = self.leads[self.current_index]['text']
        self.true_leads = [l for l in self.true_leads if l['text'] != current_text]
        self.false_leads = [l for l in self.false_leads if l['text'] != current_text]
        
        # Update display
        self.display_current_lead()
        
        # Auto-advance to next lead
        self.next_lead()
        self.reset_auto_save_timer()
    
    def previous_lead(self):
        """Go to previous lead"""
        if self.current_index > 0:
            self.current_index -= 1
            self.reset_auto_save_timer()
            self.display_current_lead()
    
    def next_lead(self):
        """Go to next lead"""
        if self.current_index < len(self.leads) - 1:
            self.current_index += 1
            self.reset_auto_save_timer()
            self.display_current_lead()
        else:
            messagebox.showinfo("Info", "You've reached the last lead!")
    
    def jump_to_lead(self):
        """Jump to a specific lead number"""
        try:
            lead_num = int(self.jump_entry.get())
            if 1 <= lead_num <= len(self.leads):
                self.current_index = lead_num - 1
                self.reset_auto_save_timer()
                self.display_current_lead()
            else:
                messagebox.showerror("Error", f"Lead number must be between 1 and {len(self.leads)}")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    def reset_auto_save_timer(self):
        """Reset the auto-save timer"""
        # Cancel existing timer
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        
        # Start new timer
        self.auto_save_timer = self.root.after(self.auto_save_delay, self.auto_save_progress)
        
        # Update status
        self.auto_save_label.config(text="Auto-save in 10s...", foreground="orange")
    
    def auto_save_progress(self):
        """Auto-save progress without showing popup"""
        try:
            self.save_progress_silent()
            self.auto_save_label.config(text="Auto-saved ✓", foreground="green")
            
            # Clear the status after 3 seconds
            self.root.after(3000, lambda: self.auto_save_label.config(text=""))
        except Exception as e:
            self.auto_save_label.config(text="Auto-save failed ✗", foreground="red")
            print(f"Auto-save error: {e}")
    
    def save_progress_silent(self):
        """Save current progress to files silently"""
        # Save true leads (job opportunities)
        with open('classified_leads.jsonl', 'w', encoding='utf-8') as f:
            for lead in self.true_leads:
                f.write(json.dumps(lead) + '\n')
        
        # Save false leads (non-job opportunities)
        with open('nonleads.jsonl', 'w', encoding='utf-8') as f:
            for lead in self.false_leads:
                f.write(json.dumps(lead) + '\n')
        
        # Save session state
        session_data = {
            'current_index': self.current_index,
            'reviewed_indices': list(self.reviewed_indices),
            'deleted_leads': list(self.deleted_leads),
            'true_count': len(self.true_leads),
            'false_count': len(self.false_leads)
        }
        with open('classifier_session.json', 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
    
    def manual_save_progress(self):
        """Manually save progress with confirmation popup"""
        try:
            self.save_progress_silent()
            messagebox.showinfo("Success", 
                f"Progress saved!\n"
                f"• Job opportunities: {len(self.true_leads)} → classified_leads.jsonl\n"
                f"• Non-jobs: {len(self.false_leads)} → nonleads.jsonl\n"
                f"• Deleted leads: {len(self.deleted_leads)} (excluded from files)\n"
                f"• Session state saved to classifier_session.json"
            )
            self.reset_auto_save_timer()  # Reset timer after manual save
        except Exception as e:
            messagebox.showerror("Error", f"Error saving files: {str(e)}")
    
    def save_progress(self):
        """Legacy method - redirects to manual save"""
        self.manual_save_progress()
    
    def load_previous_session(self):
        """Load previous classification session"""
        try:
            if os.path.exists('classifier_session.json'):
                with open('classifier_session.json', 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                self.current_index = session_data.get('current_index', 0)
                self.reviewed_indices = set(session_data.get('reviewed_indices', []))
                self.deleted_leads = set(session_data.get('deleted_leads', []))
                
                # Load previously classified leads
                if os.path.exists('classified_leads.jsonl'):
                    self.true_leads = []
                    with open('classified_leads.jsonl', 'r', encoding='utf-8') as f:
                        for line in f:
                            self.true_leads.append(json.loads(line.strip()))
                
                if os.path.exists('nonleads.jsonl'):
                    self.false_leads = []
                    with open('nonleads.jsonl', 'r', encoding='utf-8') as f:
                        for line in f:
                            self.false_leads.append(json.loads(line.strip()))
                
                self.display_current_lead()
                self.reset_auto_save_timer()  # Restart auto-save timer
                messagebox.showinfo("Success", 
                    f"Previous session loaded successfully!\n"
                    f"• Reviewed leads: {len(self.reviewed_indices)}\n"
                    f"• Classified job opportunities: {len(self.true_leads)}\n"
                    f"• Classified non-jobs: {len(self.false_leads)}"
                )
            else:
                messagebox.showinfo("Info", "No previous session found.")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading session: {str(e)}")
    
    def load_session_silently(self):
        """Load previous session data silently without popup"""
        try:
            if os.path.exists('classifier_session.json'):
                with open('classifier_session.json', 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                self.current_index = session_data.get('current_index', 0)
                self.reviewed_indices = set(session_data.get('reviewed_indices', []))
                
                # Load previously classified leads
                if os.path.exists('classified_leads.jsonl'):
                    self.true_leads = []
                    with open('classified_leads.jsonl', 'r', encoding='utf-8') as f:
                        for line in f:
                            self.true_leads.append(json.loads(line.strip()))
                
                if os.path.exists('nonleads.jsonl'):
                    self.false_leads = []
                    with open('nonleads.jsonl', 'r', encoding='utf-8') as f:
                        for line in f:
                            self.false_leads.append(json.loads(line.strip()))
                
                print(f"Session loaded silently: {len(self.reviewed_indices)} leads reviewed")
        except Exception as e:
            print(f"Could not load previous session: {e}")
    
    def save_and_exit(self):
        """Save progress and exit application"""
        # Cancel auto-save timer
        if self.auto_save_timer:
            self.root.after_cancel(self.auto_save_timer)
        
        self.manual_save_progress()
        self.root.quit()

def main():
    root = tk.Tk()
    app = LeadClassifierGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
