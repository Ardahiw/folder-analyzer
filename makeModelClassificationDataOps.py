import os

class DataFolderAnalyzer:
    """
    Hedef dizindeki klasörleri analiz eden ve görüntü sayılarına göre kategorilere ayıran sınıf
    """

    IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    def __init__(self, targetDirectory, mode="Recursive"):
        """
        ImageAnalyzer sınıfını başlatır

        Args:
            targetDirectory (str): Analiz edilecek hedef dizin yolu
        """

        self.targetDirectory = targetDirectory
        self.mode = mode
        self.categories = {
            '0-5': 0,  # 5 ve altı
            '6-25': 0,  # 6-25 arası
            '26-50': 0,  # 26-50 arası
            '50+': 0  # 50 üstü
        }
        self.folderDetails = []
        self.totalImages = 0
        self.totalFolders = 0

    def analyze(self):
        print(f"🔍 Analiz ediliyor: {self.targetDirectory}")
        print(f"Mod: {self.mode}\n")

        if self.mode == "Standart":
            self._analyze_standard()

        elif self.mode == "Recursive":
            self._analyze_recursive()

        return self.categories, self.folderDetails, self.totalImages, self.totalFolders

    def _analyze_standard(self):
        for folder in os.listdir(self.targetDirectory):
            folder_path = os.path.join(self.targetDirectory, folder)

            if os.path.isdir(folder_path):
                image_count = 0

                for file in os.listdir(folder_path):
                    if file.lower().endswith((self.IMAGE_EXTENSIONS)):
                        image_count += 1

                self._save_result(folder, folder_path, image_count)

    def _analyze_recursive(self):
        for folder in os.listdir(self.targetDirectory):
            folder_path = os.path.join(self.targetDirectory, folder)

            if os.path.isdir(folder_path):
                image_count = 0

                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        if file.lower().endswith((self.IMAGE_EXTENSIONS)):
                            image_count += 1

                self._save_result(folder, folder_path, image_count)

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

        print(f"📁 {folder}: {imageCount} görüntü ({category})")

    def _getCategory(self, imageCount):
        """
        Görüntü sayısına göre kategori belirler

        Args:
            imageCount (int): Görüntü sayısı

        Returns:
            str: Kategori adı
        """
        if imageCount <= 5:
            return '0-5'
        elif imageCount <= 25:
            return '6-25'
        elif imageCount <= 50:
            return '26-50'
        else:
            return '50+'

    def printReport(self):
        """
        Analiz sonuçlarını rapor olarak yazdırır
        """
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

        # Kategori dağılımını göster
        for category, count in self.categories.items():
            percentage = (count / self.totalFolders * 100) if self.totalFolders > 0 else 0
            bar = "█" * int(percentage / 2) + "░" * (50 - int(percentage / 2))
            print(f"{category:8} : {count:4} klasör ({percentage:5.1f}%) {bar}")

        print("\n" + "-" * 60)
        print("📋 DETAYLI LİSTE (görüntü sayısına göre sıralı):")
        print("-" * 60)

        # Görüntü sayısına göre sırala (çoktan aza)
        sortedDetails = self._getSortedDetails()

        for item in sortedDetails[:20]:  # İlk 20'yi göster
            print(f"{item['count']:4} görüntü - {item['folder']} [{item['category']}]")

        if len(sortedDetails) > 20:
            print(f"... ve {len(sortedDetails) - 20} klasör daha")

        print("\n" + "=" * 60)

        # Özet istatistikler
        self._printSummaryStats(sortedDetails)

    def _getSortedDetails(self):
        """
        Klasör detaylarını görüntü sayısına göre sıralar (çoktan aza)

        Returns:
            list: Sıralanmış klasör detayları
        """
        return sorted(self.folderDetails, key=lambda x: x['count'], reverse=True)

    def _printSummaryStats(self, sortedDetails):
        """
        Özet istatistikleri yazdırır

        Args:
            sortedDetails (list): Sıralanmış klasör detayları
        """
        print("\n📈 ÖZET İSTATİSTİKLER:")

        if sortedDetails:
            print(f"En fazla görüntü: {sortedDetails[0]['count']} - {sortedDetails[0]['folder']}")
            print(f"En az görüntü: {sortedDetails[-1]['count']} - {sortedDetails[-1]['folder']}")

        # Boş klasörler
        emptyFolders = self._getEmptyFolders()
        if emptyFolders:
            print(f"\n⚠️  Boş klasör sayısı: {len(emptyFolders)}")
            for folder in emptyFolders[:5]:  # İlk 5 boş klasörü göster
                print(f"   - {folder['folder']}")
            if len(emptyFolders) > 5:
                print(f"   ... ve {len(emptyFolders) - 5} boş klasör daha")

    def _getEmptyFolders(self):
        """
        Boş klasörleri döndürür

        Returns:
            list: Görüntü içermeyen klasörler
        """
        return [f for f in self.folderDetails if f['count'] == 0]

    def getLowImageFolders(self, threshold=5):
        """
        Belirtilen eşik değerinden az görüntü içeren klasörleri döndürür

        Args:
            threshold (int): Eşik değeri (varsayılan: 5)

        Returns:
            list: Eşik değerinden az görüntü içeren klasörler
        """
        return [f for f in self.folderDetails if f['count'] <= threshold]

    def printLowImageFolders(self, threshold=5):
        """
        Belirtilen eşik değerinden az görüntü içeren klasörleri yazdırır

        Args:
            threshold (int): Eşik değeri (varsayılan: 5)
        """
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
        """
        Kategori istatistiklerini döndürür

        Returns:
            dict: Kategori istatistikleri
        """
        stats = {}
        for category, count in self.categories.items():
            percentage = (count / self.totalFolders * 100) if self.totalFolders > 0 else 0
            stats[category] = {
                'count': count,
                'percentage': percentage
            }
        return stats

    def getFoldersByCategory(self, category):
        """
        Belirtilen kategorideki klasörleri döndürür

        Args:
            category (str): Kategori adı ('0-5', '6-25', '26-50', '50+')

        Returns:
            list: Belirtilen kategorideki klasörler
        """
        return [f for f in self.folderDetails if f['category'] == category]

