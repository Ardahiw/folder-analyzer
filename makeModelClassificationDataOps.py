import os


class DataFolderAnalyzer:
    """
    Hedef dizindeki klasörleri analiz eden ve görüntü sayılarına göre kategorilere ayıran sınıf.
    İsteğe bağlı olarak analiz ilerlemesi UI'ya callback ile aktarılabilir.
    """

    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    def __init__(self, targetDirectory, mode="Recursive", progress_callback=None, status_callback=None):
        self.targetDirectory = targetDirectory
        self.mode = mode
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        self.categories = {
            '0-5': 0,
            '6-25': 0,
            '26-50': 0,
            '50+': 0
        }
        self.folderDetails = []
        self.totalImages = 0
        self.totalFolders = 0

    def analyze(self):
        if not os.path.isdir(self.targetDirectory):
            raise FileNotFoundError(f"Geçersiz klasör yolu: {self.targetDirectory}")

        folders = [
            folder for folder in os.listdir(self.targetDirectory)
            if os.path.isdir(os.path.join(self.targetDirectory, folder))
        ]

        total_steps = max(len(folders), 1)
        self._notify_status(f"{len(folders)} klasör taranıyor...")
        self._notify_progress(0.0, 0, len(folders), "Analiz hazırlanıyor...")

        if self.mode == "Standart":
            self._analyze_standard(folders, total_steps)
        elif self.mode == "Recursive":
            self._analyze_recursive(folders, total_steps)
        else:
            raise ValueError(f"Desteklenmeyen analiz modu: {self.mode}")

        self._notify_progress(1.0, len(folders), len(folders), "Analiz tamamlandı")
        return self.categories, self.folderDetails, self.totalImages, self.totalFolders

    def _analyze_standard(self, folders, total_steps):
        for index, folder in enumerate(folders, start=1):
            folder_path = os.path.join(self.targetDirectory, folder)
            image_count = 0

            for file in os.listdir(folder_path):
                if file.lower().endswith(self.IMAGE_EXTENSIONS):
                    image_count += 1

            self._save_result(folder, folder_path, image_count)
            self._notify_progress(index / total_steps, index, len(folders), f"Taranıyor: {folder}")

    def _analyze_recursive(self, folders, total_steps):
        for index, folder in enumerate(folders, start=1):
            folder_path = os.path.join(self.targetDirectory, folder)
            image_count = 0

            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.lower().endswith(self.IMAGE_EXTENSIONS):
                        image_count += 1

            self._save_result(folder, folder_path, image_count)
            self._notify_progress(index / total_steps, index, len(folders), f"Taranıyor: {folder}")

    def _save_result(self, folder, folderPath, imageCount):
        self.totalImages += imageCount
        self.totalFolders += 1

        category = self._getCategory(imageCount)
        self.categories[category] += 1

        self.folderDetails.append({
            'folder': folder,
            'path': folderPath,
            'count': imageCount,
            'category': category
        })

    def _getCategory(self, imageCount):
        if imageCount <= 5:
            return '0-5'
        elif imageCount <= 25:
            return '6-25'
        elif imageCount <= 50:
            return '26-50'
        return '50+'

    def _notify_progress(self, progress_ratio, current, total, message):
        if self.progress_callback:
            self.progress_callback(progress_ratio, current, total, message)

    def _notify_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def printReport(self):
        print("\n" + "=" * 60)
        print("📊 GÖRÜNTÜ ANALİZ RAPORU")
        print("=" * 60)

        print(f"\n📂 Toplam Klasör Sayısı: {self.totalFolders}")
        print(f"🖼️  Toplam Görüntü Sayısı: {self.totalImages}")

        if self.totalFolders > 0:
            print(f"📊 Ortalama Görüntü Sayısı: {self.totalImages / self.totalFolders:.2f}")

        print("\n" + "-" * 60)
        print("KATEGORİLERE GÖRE DAĞILIM:")
        print("-" * 60)

        for category, count in self.categories.items():
            percentage = (count / self.totalFolders * 100) if self.totalFolders > 0 else 0
            bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
            print(f"{category:8} : {count:4} klasör ({percentage:5.1f}%) {bar}")

        print("\n" + "-" * 60)
        print("📋 DETAYLI LİSTE (görüntü sayısına göre sıralı):")
        print("-" * 60)

        sorted_details = self._getSortedDetails()
        for item in sorted_details[:20]:
            print(f"{item['count']:4} görüntü - {item['folder']} [{item['category']}]")

        if len(sorted_details) > 20:
            print(f"... ve {len(sorted_details) - 20} klasör daha")

        print("\n" + "=" * 60)
        self._printSummaryStats(sorted_details)

    def _getSortedDetails(self):
        return sorted(self.folderDetails, key=lambda x: x['count'], reverse=True)

    def _printSummaryStats(self, sortedDetails):
        print("\n📈 ÖZET İSTATİSTİKLER:")

        if sortedDetails:
            print(f"En fazla görüntü: {sortedDetails[0]['count']} - {sortedDetails[0]['folder']}")
            print(f"En az görüntü: {sortedDetails[-1]['count']} - {sortedDetails[-1]['folder']}")

        emptyFolders = self._getEmptyFolders()
        if emptyFolders:
            print(f"\n⚠️  Boş klasör sayısı: {len(emptyFolders)}")
            for folder in emptyFolders[:5]:
                print(f"   - {folder['folder']}")
            if len(emptyFolders) > 5:
                print(f"   ... ve {len(emptyFolders) - 5} boş klasör daha")

    def _getEmptyFolders(self):
        return [f for f in self.folderDetails if f['count'] == 0]

    def getLowImageFolders(self, threshold=5):
        return [f for f in self.folderDetails if f['count'] <= threshold]

    def printLowImageFolders(self, threshold=5):
        lowImageFolders = self.getLowImageFolders(threshold)

        if lowImageFolders:
            print("\n" + "=" * 60)
            print(f"🔴 {threshold} VE ALTI GÖRÜNTÜ OLAN KLASÖRLER:")
            print("=" * 60)
            for folder in sorted(lowImageFolders, key=lambda x: x['count']):
                print(f"   {folder['count']} görüntü - {folder['folder']}")
        else:
            print(f"\n✅ {threshold} ve altı görüntü içeren klasör bulunamadı.")

    def getCategoryStats(self):
        stats = {}
        for category, count in self.categories.items():
            percentage = (count / self.totalFolders * 100) if self.totalFolders > 0 else 0
            stats[category] = {
                'count': count,
                'percentage': percentage
            }
        return stats

    def getFoldersByCategory(self, category):
        return [f for f in self.folderDetails if f['category'] == category]
