import re

def clean_raw_reference(raw_text: str) -> str:
    if not raw_text or len(raw_text) < 100:
        return raw_text
    
    # Chuẩn hóa khoảng trắng
    text = re.sub(r'\s+', ' ', raw_text).strip()
    
    # Danh sách từ khóa nhận diện "rác"
    junk_keywords = [
        'Affiliation:', 'E-mail:', 'Submitted:', 'Accepted:', 
        'Received:', 'Revised:', 'Copyright ©', 'All rights reserved',
        'published by', 'Foundation for Open Access Statistics',
        'http://www.jstatsoft.org/'
    ]
    
    # Một số keyword nhạy cảm hơn, chỉ cắt nếu xuất hiện ở cuối
    sensitive_keywords = ['Journal of ', 'Volume ', 'Issue ']
    
    lower_text = text.lower()
    min_cut_pos = len(text)
    
    for kw in junk_keywords:
        pos = lower_text.find(kw.lower())
        if pos != -1 and pos > len(text) * 0.4: 
            if pos < min_cut_pos:
                min_cut_pos = pos
                
    for kw in sensitive_keywords:
        pos = lower_text.find(kw.lower())
        if pos != -1 and pos > len(text) * 0.7: 
            if pos < min_cut_pos:
                min_cut_pos = pos
                
    if min_cut_pos < len(text):
        return text[:min_cut_pos].strip().rstrip('.,- ')
        
    return text

junk_text = """R-project.org/package=zoo. DCT2D/DCT3D: This option calculates a representation of functional data on two-or three- dimensional domains in a tensor cosine basis. For speeding up the calculations, the imple- mentation is based on the fftw3 C-library (Frigo and Johnson 2005, developer version). If the fftw3-dev library is not available during the installation of the MFPCA package, the DCT2D and DCT3D options are disabled and throw an error. After installing fftw3-dev on the sys- tem, MFPCA has to be re-installed to activate DCT2D/DCT3D. The uniExpansions entry for a cosine representation of 2D/3D elements is: R> list(type = "DCT2D", qThresh, parallel) R> list(type = "DCT3D", qThresh, parallel) The discrete cosine transformation is a real-valued variant of the fast Fourier transform (FFT) and usually results in a huge number of non-zero coefficients that mostly model "noise" and can thus be set to zero without affecting the representation of the data. The user has to supply a threshold between 0 and 1 (qThresh) that defines the proportion of coefficients to be thresholded. Setting, e.g., qThresh = 0.9 will set 90% of the coefficients to zero, leaving only the 10% of the coefficients with the highest absolute values. The coefficients are stored in a 'sparseMatrix' (package Matrix) object to reduce the memory load for the following computations. The calculations can be run in parallel for the different observations by setting the parameter parallel to TRUE (defaults to FALSE), if a parallel backend has been registered before. Affiliation: Clara Happ-Kurz Department of Statistics LMU Munich E-mail: clara.happ@stat.uni-muenchen.de Journal of Statistical Software http://www.jstatsoft.org/ published by the Foundation for Open Access Statistics http://www.foastat.org/ April 2020, Volume 93, Issue 5 Submitted: 2017-09-28 doi:10.18637/jss.v093.i05 Accepted: 2018-12-03"""

cleaned = clean_raw_reference(junk_text)
print(f"Original Length: {len(junk_text)}")
print(f"Cleaned Length: {len(cleaned)}")
print(f"Cleaned Text Ends With: {cleaned[-100:]}")

