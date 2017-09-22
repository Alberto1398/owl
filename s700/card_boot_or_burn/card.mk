CARD_DIR=$(OUT_DIR)/card_boot_or_burn
CARD_UBOOT_DIR=$(CARD_DIR)/uboot
CARD_BOOTLOAD_DIR=$(CARD_DIR)/bootloader

CARD_LINUX_KERNEL_DIR=$(CARD_DIR)/kernel

CARD_BURN_DIR=$(CARD_DIR)/card_burn
CARD_BURN_UPRAMFS_ROOTFS=$(CARD_BURN_DIR)/upramfs
CARD_BURN_MISC_DIR=$(CARD_BURN_DIR)/misc
CARD_BURN_UDISK_DIR=$(CARD_BURN_DIR)/udsik
CARD_BURN_IMAGE=$(CARD_BURN_DIR)/images

BURN_UDISK_OFFSET=$$(($(BURN_UDISK_SIZE) + 131072 - 100))

CARD_BOOT_DIR=$(CARD_DIR)/card_boot
CARD_BOOT_IMAGE_DIR=$(CARD_BOOT_DIR)/images
CARD_BOOT_MISC_DIR=$(CARD_BOOT_DIR)/misc


card_uboot:
	$(Q)echo "--build card_uboot--"
	$(Q)mkdir -p $(CARD_UBOOT_DIR)
	$(Q)$(MAKE) -C $(UBOOT_SRC) CROSS_COMPILE=$(CROSS_COMPILE) KBUILD_OUTPUT=$(CARD_UBOOT_DIR) $(UBOOT_CARD_DEFCONFIG)
	$(Q)$(MAKE) -C $(UBOOT_SRC) CROSS_COMPILE=$(CROSS_COMPILE) KBUILD_OUTPUT=$(CARD_UBOOT_DIR) -j$(CPUS) all u-boot-dtb.img
	$(Q)cp $(CARD_UBOOT_DIR)/u-boot-dtb.img $(CARD_UBOOT_DIR)/uboot.bin
	$(Q)cd $(SCRIPT_DIR) && ./padbootloader $(CARD_UBOOT_DIR)/uboot.bin

card_bootloader:
	$(Q)echo "--build card_bootloader--"
	$(Q)mkdir -p $(CARD_BOOTLOAD_DIR)
	$(Q)cp $(TOP_DIR)/$(IC_NAME)/bootloader/*.bin $(CARD_BOOTLOAD_DIR)/ ; \
	$(Q)cd $(IC_SCRIPT_DIR) && ./bootloader_pack $(BOARD_CONFIG_DIR)/bootloader_card_burn.ini $(CARD_BOOTLOAD_DIR)/bootloader.bin

card_burn_kernel:
	$(Q)mkdir -p $(CARD_LINUX_KERNEL_DIR)
	$(Q)$(MAKE) -C $(KERNEL_SRC) ARCH=$(ARCH) O=$(CARD_LINUX_KERNEL_DIR) $(KERNEL_BURN_DEFCONFIG) && \
	$(Q)$(MAKE) -C $(KERNEL_SRC) CROSS_COMPILE=$(CROSS_COMPILE) ARCH=$(ARCH) O=$(CARD_LINUX_KERNEL_DIR) -j$(CPUS) && \
	$(Q)$(MAKE) -C $(KERNEL_SRC) CROSS_COMPILE=$(CROSS_COMPILE) ARCH=$(ARCH) O=$(CARD_LINUX_KERNEL_DIR) $(KERNEL_IMAGE)


card_burn_misc_prepare:
	$(Q)echo "-- Build card_burn_misc_prepare --"
	$(Q)mkdir -p $(CARD_BURN_MISC_DIR)
	$(Q)mkdir -p $(CARD_BURN_IMAGE)
	$(Q)cp -rf $(BOARD_CONFIG_DIR)/misc/* $(CARD_BURN_MISC_DIR)/

card_burn_upramfs: 
	$(Q)echo "--build card_burn_upramfs--"
	$(Q)rm -rf $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)mkdir -p $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)rm -rf ${CARD_BURN_MISC_DIR}/ramdisk.img
	$(Q)$(SCRIPT_DIR)/populate_dir $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)cp -rf $(TOP_DIR)/$(IC_NAME)/burn/initramfs/* $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)cp -rf $(TOP_DIR)/$(IC_NAME)/burn/card_burn_initramfs/* $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)cp -rf $(TOP_DIR)/$(IC_NAME)/prebuilt/initramfs/* $(CARD_BURN_UPRAMFS_ROOTFS)
	$(Q)$(CROSS_COMPILE)strip --strip-unneeded $(CARD_BURN_UPRAMFS_ROOTFS)/lib/modules/*.ko	
	$(Q)$(SCRIPT_DIR)/gen_initramfs_list.sh -u 0 -g 0 $(CARD_BURN_UPRAMFS_ROOTFS) > $(CARD_DIR)/upramfs.list
	$(Q)${SCRIPT_DIR}/gen_init_cpio $(CARD_DIR)/upramfs.list > ${CARD_DIR}/upramfs.img.tmp
	$(Q)$(TOOLS_DIR)/utils/mkimage -n "RAMFS" -A $(ARCH) -O linux -T ramdisk -C none -a 02000000 -e 02000000 -d ${CARD_DIR}/upramfs.img.tmp ${CARD_BURN_MISC_DIR}/ramdisk.img
	$(Q)rm ${CARD_DIR}/upramfs.img.tmp
	$(Q)rm ${CARD_DIR}/upramfs.list

card_burn_misc: card_burn_misc_prepare  card_burn_upramfs card_burn_kernel
	$(Q)echo "-- Build Fat card Misc image --"
	$(Q)cp $(CARD_LINUX_KERNEL_DIR)/arch/$(ARCH)/boot/$(KERNEL_IMAGE) $(CARD_BURN_MISC_DIR)
	$(Q)cp $(CARD_LINUX_KERNEL_DIR)/arch/$(ARCH)/boot/dts/$(KERNEL_CARD_DTS).dtb $(CARD_BURN_MISC_DIR)/kernel.dtb
	$(Q)cp $(BOARD_CONFIG_DIR)/uenv.txt $(CARD_BURN_MISC_DIR)

	$(Q)dd if=/dev/zero of=$(CARD_BURN_IMAGE)/card_burn_misc.img bs=1M count=$(MISC_IMAGE_SIZE)
	$(Q)$(TOOLS_DIR)/utils/makebootfat -o $(CARD_BURN_IMAGE)/card_burn_misc.img -L misc -b $(SCRIPT_DIR)/bootsect.bin $(CARD_BURN_MISC_DIR)

card_burn_udisk:
	$(Q)echo "-- copy data to udisk --"
	$(Q)mkdir -p $(CARD_BURN_UDISK_DIR)
	$(Q)mkdir -p $(CARD_BURN_IMAGE)
	$(Q)cp $(BOARD_CONFIG_DIR)/bootloader.ini $(CARD_BURN_UDISK_DIR)
	$(Q)cp $(BOOTLOAD_DIR)/bootloader.bin $(CARD_BURN_UDISK_DIR)/
	$(Q)cp $(UBOOT_OUT_DIR)/uboot.bin $(CARD_BURN_UDISK_DIR)/
	$(Q)cp $(BOARD_CONFIG_DIR)/partition.cfg $(CARD_BURN_UDISK_DIR)/
	$(Q)cp $(IMAGE_DIR)/*.img $(CARD_BURN_UDISK_DIR)/
	$(Q)dd if=/dev/zero of=${CARD_BURN_IMAGE}/card_burn_udisk.img bs=512 count=$(BURN_UDISK_SIZE)
	$(Q)$(TOOLS_DIR)/utils/makebootfat -o ${CARD_BURN_IMAGE}/card_burn_udisk.img -L udisk -b $(SCRIPT_DIR)/bootsect.bin $(CARD_BURN_UDISK_DIR)

card_burn_pack: 
	$(Q)rm -rf $(IMAGE_DIR)/burn_image.bin
	$(Q)rm -rf $(IMAGE_DIR)/burn_image_new.bin

	$(Q)echo "-- make burn card image --"
	$(Q)dd if=$(CARD_BOOTLOAD_DIR)/bootloader.bin of=$(CARD_BURN_IMAGE)/burn_image.bin bs=512 seek=4097
	$(Q)dd if=$(CARD_UBOOT_DIR)/uboot.bin of=$(CARD_BURN_IMAGE)/burn_image.bin bs=1024 seek=3072   #3M  offset
	$(Q)dd if=${CARD_BURN_IMAGE}/card_burn_misc.img of=$(CARD_BURN_IMAGE)/burn_image.bin bs=1048576 seek=16   #16M offset
	$(Q)dd if=${CARD_BURN_IMAGE}/card_burn_udisk.img of=$(CARD_BURN_IMAGE)/burn_image.bin bs=1048576 seek=64  #64M offset

	$(Q)echo "-- create partitions --"
	$(Q)$(TOOLS_DIR)/utils/parted -s $(CARD_BURN_IMAGE)/burn_image.bin mklabel gpt
	$(Q)$(TOOLS_DIR)/utils/parted -s $(CARD_BURN_IMAGE)/burn_image.bin unit s mkpart MISC 32768 131071     #start:16M end:64M
	$(Q)$(TOOLS_DIR)/utils/parted -s $(CARD_BURN_IMAGE)/burn_image.bin unit s mkpart UDISK 131072 $$(($(BURN_UDISK_OFFSET))) #start:64M end:64M+udisk_size
	dd if=$(CARD_BURN_IMAGE)/burn_image.bin of=$(CARD_BURN_IMAGE)/burn_image_new.bin bs=512 skip=1
	$(Q)cp $(CARD_BURN_IMAGE)/burn_image.bin $(IMAGE_DIR)
	$(Q)cp $(CARD_BURN_IMAGE)/burn_image_new.bin $(IMAGE_DIR)

card_burn_image: card_uboot card_bootloader card_burn_misc card_burn_udisk card_burn_pack


card_boot_misc:
	$(Q)echo "-- Build card boot Misc image --"
	$(Q)mkdir -p $(CARD_BOOT_MISC_DIR)
	$(Q)mkdir -p $(CARD_BOOT_IMAGE_DIR)
	$(Q)cp -rf $(MISC_DIR)/modules $(CARD_BOOT_MISC_DIR)/
	$(Q)cp -r $(BOARD_CONFIG_DIR)/misc/* $(CARD_BOOT_MISC_DIR)/
	$(Q)cp $(KERNEL_OUT_DIR)/arch/$(ARCH)/boot/dts/$(KERNEL_CARD_DTS).dtb $(CARD_BOOT_MISC_DIR)/kernel.dtb
	$(Q)cp $(BOARD_CONFIG_DIR)/uenv.txt $(CARD_BOOT_MISC_DIR)

	$(Q)cp $(KERNEL_OUT_DIR)/arch/$(ARCH)/boot/$(KERNEL_IMAGE) $(CARD_BOOT_MISC_DIR)
	$(Q)cp -f $(MISC_DIR)/ramdisk.img $(CARD_BOOT_MISC_DIR)/ramdisk.img
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_misc.img bs=1M count=$(MISC_IMAGE_SIZE)
	$(Q)$(TOOLS_DIR)/utils/makebootfat -o $(CARD_BOOT_IMAGE_DIR)/card_boot_misc.img -L misc -b $(SCRIPT_DIR)/bootsect.bin $(CARD_BOOT_MISC_DIR)

card_boot_other:

	$(Q)echo "-- Build ext4 card system image --"
	simg2img $(IMAGE_DIR)/system.img $(CARD_BOOT_IMAGE_DIR)/card_boot_system.img

	$(Q)echo "-- Build Fat BOOT_MSB image --"
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_msg.img bs=1M count=1
	$(Q)mkfs.vfat $(CARD_BOOT_IMAGE_DIR)/card_boot_msg.img
	
	$(Q)echo "-- Build ext4 data image --"
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_data.img bs=1M count=512
	$(Q)echo y | mkfs.ext4 $(CARD_BOOT_IMAGE_DIR)/card_boot_data.img  

	$(Q)echo "-- Build ext4 CACHE image --"
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_cache.img bs=1M count=512
	$(Q)echo y | mkfs.ext4 $(CARD_BOOT_IMAGE_DIR)/card_boot_cache.img
	
	$(Q)echo "-- Build ext4 data_bak image --"
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_data_bak.img bs=1M count=1
	$(Q)echo y | mkfs.ext4 $(CARD_BOOT_IMAGE_DIR)/card_boot_data_bak.img 

	$(Q)echo "-- Build vfat udisk image --"
	$(Q)dd if=/dev/zero of=$(CARD_BOOT_IMAGE_DIR)/card_boot_udisk.img bs=1M count=1024
	$(Q)mkfs.vfat $(CARD_BOOT_IMAGE_DIR)/card_boot_udisk.img


card_boot_pack:
	$(Q)rm -rf $(IMAGE_DIR)/boot_image.bin
	$(Q)rm -rf $(IMAGE_DIR)/boot_image_new.bin
	$(Q)echo "-- make card_boot_pack --"
	$(Q)dd if=$(CARD_BOOTLOAD_DIR)/bootloader.bin      of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=512 seek=4097
	$(Q)dd if=$(CARD_UBOOT_DIR)/uboot.bin            of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1024 seek=3072     #3M  offset
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_misc.img       of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=16    #16M offset
	$(Q)dd if=$(IMAGE_DIR)/recovery.img   of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=64    #64M offset
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_system.img     of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=112   #112M offset
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_msg.img        of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=1672 
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_data.img       of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=1673  #seek=1673  
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_cache.img      of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=2185  #seek=2185
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_data_bak.img   of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=2697  #seek=2697
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/card_boot_udisk.img	  of=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin bs=1048576 seek=2698  #seek=2698

	#create partitions
	$(Q)$(TOOLS_DIR)/utils/parted -s $(CARD_BOOT_IMAGE_DIR)/boot_image.bin mklabel gpt
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart MISC 32768 131071                #start:16M end:64M 131038 
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart RECOVERY 131072  229375          #131072 229375 #start:64M end:112M 
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart SYSTEM 229376 3424255            #229376 1867775  #start:112M end:912M 
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart BOOT_MSG 3424256 3426303         #1867776 1869823
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart DATA 3426304 4474879             #start:1673M end:2185M 3424256 4472831 
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart CACHE 4474880 5523455            #start:2185M end:2697M 4472832 5255168  5263326
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart DATA_BAK 5523456 5525503
	$(Q)$(TOOLS_DIR)/utils/parted  $(CARD_BOOT_IMAGE_DIR)/boot_image.bin unit s mkpart UDISK 5525504 7620607			#7622655 - 2048 = 7620607,reserve 1MB for GTP BackUp
	$(Q)dd if=$(CARD_BOOT_IMAGE_DIR)/boot_image.bin of=$(CARD_BOOT_IMAGE_DIR)/boot_image_new.bin bs=512 skip=1
	$(Q)cp $(CARD_BOOT_IMAGE_DIR)/boot_image.bin $(IMAGE_DIR)
	#$(Q)cp $(CARD_BOOT_IMAGE_DIR)/boot_image_new.bin $(IMAGE_DIR)

card_boot_image: card_uboot card_bootloader card_boot_misc card_boot_other card_boot_pack

