const fs = require('fs');
const path = require('path');

// Read the leads.json file
console.log('Reading leads.json...');
const leadsData = JSON.parse(fs.readFileSync('leads.json', 'utf8'));

console.log(`Found ${leadsData.length} leads to process`);

// Transform leads into text classification format
const transformedLeads = [];

leadsData.forEach((lead, index) => {
  try {
    // Get platform name and capitalize it
    const platform = lead.platform ? lead.platform.toUpperCase() : 'UNKNOWN';
    
    let text = '';
    
    // Handle different platforms according to the rules
    if (platform === 'REDDIT') {
      // For Reddit: use title + content (if content exists)
      if (lead.content && lead.content.trim() !== '') {
        text = `[${platform}] ${lead.title} ${lead.content}`;
      } else {
        text = `[${platform}] ${lead.title}`;
      }
    } else {
      // For LinkedIn, Twitter/X, and others: just use content
      text = `[${platform}] ${lead.content || lead.title || ''}`;
    }
    
    // Clean up the text (remove extra whitespace)
    text = text.replace(/\s+/g, ' ').trim();
    
    // Only add if we have valid text
    if (text && text.length > platform.length + 3) {  // More than just "[PLATFORM] "
      transformedLeads.push({
        text: text,
        label: 1
      });
    } else {
      console.warn(`Skipping lead ${index + 1}: insufficient text content`);
    }
    
  } catch (error) {
    console.error(`Error processing lead ${index + 1}:`, error.message);
  }
});

console.log(`Successfully transformed ${transformedLeads.length} leads`);

// Write to JSONL file (one JSON object per line)
console.log('Writing to leads.jsonl...');
const jsonlContent = transformedLeads.map(lead => JSON.stringify(lead)).join('\n');

fs.writeFileSync('leads.jsonl', jsonlContent, 'utf8');

console.log(`✅ Successfully created leads.jsonl with ${transformedLeads.length} entries`);

// Show some sample entries
console.log('\nSample entries:');
transformedLeads.slice(0, 5).forEach((lead, index) => {
  console.log(`${index + 1}. ${lead.text.substring(0, 100)}${lead.text.length > 100 ? '...' : ''}`);
});

// Show platform distribution
const platformCounts = {};
transformedLeads.forEach(lead => {
  const platform = lead.text.match(/\[([^\]]+)\]/)?.[1] || 'UNKNOWN';
  platformCounts[platform] = (platformCounts[platform] || 0) + 1;
});

console.log('\nPlatform distribution:');
Object.entries(platformCounts).forEach(([platform, count]) => {
  console.log(`${platform}: ${count} leads`);
});
