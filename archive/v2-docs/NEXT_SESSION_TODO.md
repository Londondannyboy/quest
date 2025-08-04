# Next Session TODO
*Updated: July 24, 2025*

> **Major Achievement**: Apify LinkedIn Scraping Fixed and Working! 🎉  
> **Next Goal**: Implement "Shock & Awe" LinkedIn Registration Flow

## ✅ **TODAY'S ACHIEVEMENT: Apify Integration Complete**
- **Root Cause Found**: harvestapi/linkedin-profile-scraper returns data in `items[0].element`
- **Fix Applied**: `const profile = item.element || item;`
- **Production Ready**: Working on both local and Vercel deployments
- **Test Verified**: Successfully scraping real LinkedIn profiles
- **Documentation**: Complete troubleshooting guide and solutions documented

## 🎯 **TOMORROW'S PRIORITY: LinkedIn Registration Flow**

### **Priority 1: Implement LinkedIn Import in Registration**
**Status**: Unblocked and ready to build  
**Time Estimate**: 3-4 hours

**Tasks**:
1. [ ] Create `/register/linkedin-import` page
2. [ ] Add LinkedIn URL input field
3. [ ] Implement scraping on form submission
4. [ ] Map LinkedIn data to Quest profile:
   - `element.firstName` + `element.lastName` → name fields
   - `element.headline` → professionalHeadline
   - `element.location.linkedinText` → location
   - `element.experience[]` → UserWorkExperience
   - `element.education[]` → UserEducation
   - `element.skills[]` → UserSkills
5. [ ] Show preview of imported data
6. [ ] Allow editing before final submission
7. [ ] Create user account with enriched data

### **Priority 2: Company Data Enrichment**
**Status**: Ready to implement using same pattern  
**Time Estimate**: 2 hours

**Tasks**:
1. [ ] Extract companies from user's experience
2. [ ] Implement company scraper using Apify
3. [ ] Store company data in database
4. [ ] Link user to companies
5. [ ] Build company relationship graph

### **Priority 3: OpenRouter Integration Completion**
**Status**: Environment variable set, needs implementation  
**Time Estimate**: 2-3 hours

**Tasks**:
1. [ ] Complete AI client abstraction
2. [ ] Configure model routing per coach type
3. [ ] Test each coach with appropriate model
4. [ ] Implement cost tracking
5. [ ] Add fallback logic

## 🔧 **Technical Notes from Today**

### **Apify Data Structure (IMPORTANT)**
```javascript
// Data is nested in element field:
const result = await apifyClient.dataset(run.defaultDatasetId).listItems();
const profile = result.items[0].element; // ← Not result.items[0] directly!

// Profile structure:
{
  element: {
    firstName: "Bill",
    lastName: "Gates", 
    headline: "...",
    location: { linkedinText: "Seattle, WA" },
    experience: [...],
    education: [...],
    skills: [...]
  }
}
```

### **Working Test Endpoints**
- `/api/test-profile-simple` - Main scraping endpoint (FIXED)
- `/admin/test-scraping` - Admin UI for testing
- `/api/debug-apify-env` - Environment variable checker

## 📊 **Quick Wins for Tomorrow**

1. **Simple LinkedIn Import**
   - Basic form → Scrape → Show data
   - No fancy UI needed initially
   - Focus on data accuracy

2. **Profile Preview Component**
   - Show scraped data clearly
   - Highlight imported vs manual fields
   - Allow corrections

3. **Success Metrics**
   - Import completes in < 30 seconds
   - All major fields populated
   - User can edit before saving

## 🧪 **Testing Checklist**

- [ ] Test with various LinkedIn profiles
- [ ] Handle private/restricted profiles
- [ ] Verify data mapping accuracy
- [ ] Test with incomplete profiles
- [ ] Ensure Clerk integration still works
- [ ] Check database persistence

## 📝 **Lessons Learned Today**

1. **Always inspect actual API responses** - Assumed data structure was wrong
2. **Simple debugging tools save time** - Standalone scripts revealed issue quickly
3. **Official SDKs work best** - apify-client package works perfectly
4. **Document data structures** - Will save future debugging time

## 🚀 **Week Goals**

1. **Monday**: LinkedIn registration flow
2. **Tuesday**: Company enrichment + employee discovery
3. **Wednesday**: Complete OpenRouter + multi-coach
4. **Thursday**: Zep memory integration
5. **Friday**: Trinity system foundation

---

**Remember**: The key to Apify is that profile data is in `items[0].element`. This applies to all Harvest API scrapers!