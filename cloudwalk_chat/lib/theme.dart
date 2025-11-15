import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  // Paleta inspirada na InfinitePay
  static const primary = Color(0xFF6A39F0); // roxo
  static const primaryDark = Color(0xFF4C2AC0);
  static const accent = Color(0xFF00E1B0); // turquesa
  static const surface = Color(0xFFF7F6FF); // fundo claro
  static const textPrimary = Color(0xFF0F0B26);
  static const textSecondary = Color(0xFF5C5873);

  static const bubbleUserGradA = Color(0xFF7B46FF);
  static const bubbleUserGradB = Color(0xFF5B2DDB);
  static const bubbleBot = Color(0xFFF0EDFF);
}

ThemeData buildAppTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: AppColors.primary,
    primary: AppColors.primary,
    secondary: AppColors.accent,
    background: AppColors.surface,
    brightness: Brightness.light,
  );

  final textTheme = GoogleFonts.interTextTheme().copyWith(
    titleLarge: GoogleFonts.inter(
      fontWeight: FontWeight.w700,
      color: AppColors.textPrimary,
    ),
    bodyMedium: GoogleFonts.inter(color: AppColors.textPrimary),
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    textTheme: textTheme,
    scaffoldBackgroundColor: AppColors.surface,
    appBarTheme: AppBarTheme(
      backgroundColor: Colors.transparent,
      elevation: 0,
      centerTitle: false,
      titleTextStyle: GoogleFonts.inter(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: AppColors.textPrimary,
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: const Color(0xFFE7E4F6)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: BorderSide(color: const Color(0xFFE7E4F6)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(14),
        borderSide: const BorderSide(color: AppColors.primary, width: 1.6),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: AppColors.primary,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      ),
    ),
    chipTheme: ChipThemeData(
      backgroundColor: AppColors.bubbleBot,
      labelStyle: GoogleFonts.inter(color: AppColors.textSecondary),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
    ),
  );
}
