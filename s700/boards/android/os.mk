
#candidate: userdebug, eng, user
lunch_type=userdebug

R_OS_DIR=$(TOP_DIR)/../android
FW_RECOVERY=$(OUT_DIR)/recovery
MINIOTA_OUT_DIR=$(OUT_DIR)/miniOta
BOOTBIN_DIR=$(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/bootbin
PRODUCT_OUT=$(R_OS_DIR)/out/target/product/$(ANDROID_BOARD)
PRODUCT_PREBUILD_DIR=$(TOP_DIR)/$(IC_NAME)/prebuilt


.PHONY: system recovery ota miniOta

system:
	$(Q)rm -rf $(MISC_DIR)/modules
	$(Q)mkdir -p $(MISC_DIR)/modules
	$(Q)mkdir -p $(IMAGE_DIR)
	$(Q)find $(KERNEL_OUT_DIR) -name '*.ko' | xargs cp -t $(MISC_DIR)/modules
	$(Q)$(CROSS_COMPILE)strip --strip-unneeded $(MISC_DIR)/modules/*.ko
	$(Q)cp $(PRODUCT_PREBUILD_DIR)/initramfs/lib/modules/*.ko $(R_OS_DIR)/device/actions/common/prebuilt/utils/driver/s700
	$(Q)cp $(MISC_DIR)/modules/ctp_gt9xx.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/libcomposite.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/usb_f_acm.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/ctp_gslX680.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/g_android.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/ctp_ft5x06.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cp $(MISC_DIR)/modules/u_serial.ko $(R_OS_DIR)/device/actions/$(ANDROID_BOARD)/recovery/
	$(Q)cd $(R_OS_DIR) && source build/envsetup.sh && lunch $(ANDROID_BOARD)-$(lunch_type) && $(MAKE) -j$(CPUS)
	$(Q)$(TOOLS_DIR)/utils/mkimage -n "RAMFS" -A $(ARCH) -O linux -T ramdisk -C none -a 02000000 -e 02000000 -d $(PRODUCT_OUT)/ramdisk.img $(MISC_DIR)/ramdisk.img
	$(Q)cp $(PRODUCT_OUT)/system.img $(IMAGE_DIR)/
	$(Q)mkdir -p $(FW_RECOVERY)
	$(Q)$(TOOLS_DIR)/utils/mkimage -n "RAMFS" -A $(ARCH) -O linux -T ramdisk -C none -a 02000000 -e 02000000 -d $(PRODUCT_OUT)/ramdisk-recovery.img $(FW_RECOVERY)/ramdisk.img

recovery:
	@echo "-- Build Fat Recovery image --"
	$(Q)mkdir -p $(FW_RECOVERY)
	$(Q)cp -r $(BOARD_CONFIG_DIR)/misc/* $(FW_RECOVERY)/
	$(Q)cp $(KERNEL_OUT_DIR)/arch/$(ARCH)/boot/$(KERNEL_IMAGE) $(FW_RECOVERY)
	$(Q)cp $(KERNEL_OUT_DIR)/arch/$(ARCH)/boot/dts/$(KERNEL_DTS).dtb $(FW_RECOVERY)/kernel.dtb
	
	@echo "--Fix vmlinux.bin.."
	$(Q)dd if=/dev/zero of=$(IMAGE_DIR)/recovery.img bs=1M count=$(RECOVERY_IMAGE_SIZE)
	$(Q)$(TOOLS_DIR)/utils/makebootfat -o $(IMAGE_DIR)/recovery.img -L recovery -b $(SCRIPT_DIR)/bootsect.bin $(FW_RECOVERY)

ota:
	@echo "-- Build ota --"
	$(Q)mkdir -p $(BOOTBIN_DIR)
	$(Q)cp $(IMAGE_DIR)/misc.img $(BOOTBIN_DIR)
	$(Q)cp $(IMAGE_DIR)/recovery.img $(BOOTBIN_DIR)
	$(Q)cd $(R_OS_DIR) && source build/envsetup.sh && lunch $(ANDROID_BOARD)-$(lunch_type) && $(MAKE) otapackage -j$(CPUS)
	$(Q)cp $(PRODUCT_OUT)/*.zip $(IMAGE_DIR)/

miniOta:
	$(Q)rm -rf $(MINIOTA_OUT_DIR)
	$(Q)mkdir -p $(MINIOTA_OUT_DIR)
	$(Q)cd $(IMAGE_DIR) && cp $(ANDROID_BOARD)-ota-eng*.zip $(MINIOTA_OUT_DIR)
	$(Q)cd $(MINIOTA_OUT_DIR) && unzip -q $(ANDROID_BOARD)-ota-eng*.zip -d . && \
	$(Q)rm -rf system* recovery.img misc.img $(ANDROID_BOARD)-ota-eng*.zip
	$(Q)cd $(SCRIPT_DIR) && cp ./ImgShowName.bin $(MINIOTA_OUT_DIR)
	$(Q)cd $(MINIOTA_OUT_DIR) && zip -qry $(MINIOTA_OUT_DIR)/mini_ota.zip .

rootfs: system recovery misc ota miniOta

rootfs_clean:
	$(Q)cd $(R_OS_DIR) && source build/envsetup.sh && lunch $(ANDROID_BOARD)-$(lunch_type) && $(MAKE) clean
